"""ZAP Authenticator in a Python Thread.

.. versionadded:: 14.1
"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import asyncio
import logging
from itertools import chain
from threading import Event, Thread
from typing import Any, Dict, List, Optional, TypeVar, cast

import zmq
import zmq.asyncio
from zmq.utils import jsonapi

from .asyncio import AsyncioAuthenticator
from .base import Authenticator


class AuthenticationThread(Thread):
    """A Thread for running a zmq Authenticator

    This is run in the background by ThreadAuthenticator
    """

    pipe: zmq.Socket
    loop: asyncio.AbstractEventLoop
    authenticator: AsyncioAuthenticator
    poller: Optional[zmq.asyncio.Poller]

    def __init__(
        self,
        context: zmq.Context,
        endpoint: str,
        encoding: str = 'utf-8',
        log: Any = None,
    ) -> None:
        super().__init__()

        self.context = context
        self.endpoint = endpoint
        self.encoding = encoding
        self.log = log or logging.getLogger('zmq.auth')

        self.started = Event()

    def run(self) -> None:
        """Start the Authentication Agent thread task"""

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._run())
        finally:
            if self.poller:
                self.poller.unregister(self.pipe)
                self.poller = None
            if self.authenticator:
                self.authenticator.stop()
                self.authenticator = None  # type: ignore
            if self.pipe:
                self.pipe.close()
                self.pipe = None  # type: ignore

            loop.close()

    async def _run(self):

        # create a socket to communicate back to main thread.
        self.pipe: zmq.Socket = self.context.socket(zmq.PAIR, socket_class=zmq.Socket)
        self.pipe.linger = 1
        self.pipe.connect(self.endpoint)

        self.authenticator = AsyncioAuthenticator(
            self.context, encoding=self.encoding, log=self.log
        )
        self.authenticator.start()

        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.pipe, zmq.POLLIN)
        self.started.set()

        while True:
            events = await self.poller.poll()
            if self.pipe in dict(events):
                msg = self.pipe.recv_multipart()
                if self.__handle_pipe_message(msg):
                    return

    def __handle_pipe_message(self, msg: List[bytes]) -> bool:
        if msg is None:
            return True

        command = msg[0]
        self.log.debug("auth received API command %r", command)

        if command == b'ALLOW':
            addresses = [m.decode(self.encoding) for m in msg[1:]]
            try:
                self.authenticator.allow(*addresses)
            except Exception:
                self.log.exception(f"Failed to allow {addresses}")
                self.pipe.send(b'ERROR')
            else:
                self.pipe.send(b'OK')

        elif command == b'DENY':
            addresses = [m.decode(self.encoding) for m in msg[1:]]
            try:
                self.authenticator.deny(*addresses)
            except Exception:
                self.log.exception(f"Failed to deny {addresses}")
                self.pipe.send(b'ERROR')
            else:
                self.pipe.send(b'OK')

        elif command == b'PLAIN':
            domain = msg[1].decode(self.encoding)
            json_passwords = msg[2]
            passwords: Dict[str, str] = cast(
                Dict[str, str], jsonapi.loads(json_passwords)
            )
            try:
                self.authenticator.configure_plain(domain, passwords)
            except Exception:
                self.log.exception(f"Failed to set up plain auth for {domain}")
                self.pipe.send(b'ERROR')
            else:
                self.pipe.send(b'OK')

        elif command == b'CURVE':
            # For now we don't do anything with domains
            domain = msg[1].decode(self.encoding)

            # If location is CURVE_ALLOW_ANY, allow all clients. Otherwise
            # treat location as a directory that holds the certificates.
            location = msg[2].decode(self.encoding)
            try:
                self.authenticator.configure_curve(domain, location)
            except Exception:
                self.log.exception(f"Failed to set up curve auth for {domain}")
                self.pipe.send(b'ERROR')
            else:
                self.pipe.send(b'OK')

        elif command == b'TERMINATE':
            return True

        else:
            self.log.error("Invalid auth command from API: %r", command)
            self.pipe.send(b'ERROR')

        return False


T = TypeVar("T", bound=type)


def _inherit_docstrings(cls: T) -> T:
    """inherit docstrings from Authenticator, so we don't duplicate them"""
    for name, method in cls.__dict__.items():
        if name.startswith('_') or not callable(method):
            continue
        upstream_method = getattr(Authenticator, name, None)
        if not method.__doc__:
            method.__doc__ = upstream_method.__doc__
    return cls


@_inherit_docstrings
class ThreadAuthenticator:
    """Run ZAP authentication in a background thread"""

    context: "zmq.Context"
    log: Any
    encoding: str
    pipe: "zmq.Socket"
    pipe_endpoint: str = ''
    thread: AuthenticationThread
    _pipe_poller: "zmq.Poller"
    _pipe_reply_timeout_seconds: float = 3

    def __init__(
        self,
        context: Optional["zmq.Context"] = None,
        encoding: str = 'utf-8',
        log: Any = None,
    ):
        self.log = log
        self.encoding = encoding
        self.pipe = None  # type: ignore
        self.pipe_endpoint = f"inproc://{id(self)}.inproc"
        self.thread = None  # type: ignore
        self.context = context or zmq.Context.instance()

    # proxy base Authenticator attributes

    def __setattr__(self, key: str, value: Any):
        for obj in chain([self], self.__class__.mro()):
            if key in obj.__dict__ or (key in getattr(obj, "__annotations__", {})):
                object.__setattr__(self, key, value)
                return
        setattr(self.thread.authenticator, key, value)

    def __getattr__(self, key: str):
        if self.thread and hasattr(self.thread, "authenticator"):
            return getattr(self.thread.authenticator, key)
        else:
            raise AttributeError(key)

    def _pipe_request(self, msg):
        """Check the reply on the pipe"""
        self.pipe.send_multipart(msg)
        evts = self._pipe_poller.poll(
            timeout=int(1000 * self._pipe_reply_timeout_seconds)
        )
        if not evts:
            raise RuntimeError("Auth thread never responded")
        reply = self.pipe.recv_multipart()
        if reply != [b"OK"]:
            raise RuntimeError("Error in auth thread, check logs")

    def allow(self, *addresses: str):
        self._pipe_request([b'ALLOW'] + [a.encode(self.encoding) for a in addresses])

    def deny(self, *addresses: str):
        self._pipe_request([b'DENY'] + [a.encode(self.encoding) for a in addresses])

    def configure_plain(
        self, domain: str = '*', passwords: Optional[Dict[str, str]] = None
    ):
        self._pipe_request(
            [b'PLAIN', domain.encode(self.encoding), jsonapi.dumps(passwords or {})]
        )

    def configure_curve(self, domain: str = '*', location: str = ''):
        domain = domain.encode(self.encoding)
        location = location.encode(self.encoding)
        self._pipe_request([b'CURVE', domain, location])

    def configure_curve_callback(
        self, domain: str = '*', credentials_provider: Any = None
    ):
        self.thread.authenticator.configure_curve_callback(
            domain, credentials_provider=credentials_provider
        )

    def start(self) -> None:
        """Start the authentication thread"""
        # create a socket to communicate with auth thread.
        self.pipe = self.context.socket(zmq.PAIR, socket_class=zmq.Socket)
        self._pipe_poller = zmq.Poller()
        self._pipe_poller.register(self.pipe, zmq.POLLIN)
        self.pipe.linger = 1
        self.pipe.bind(self.pipe_endpoint)
        self.thread = AuthenticationThread(
            self.context, self.pipe_endpoint, encoding=self.encoding, log=self.log
        )
        self.thread.start()
        if not self.thread.started.wait(timeout=10):
            raise RuntimeError("Authenticator thread failed to start")

    def stop(self) -> None:
        """Stop the authentication thread"""
        if self.pipe:
            self.pipe.send(b'TERMINATE')
            if self.is_alive():
                self.thread.join()
            self.thread = None  # type: ignore
            self.pipe.close()
            self.pipe = None  # type: ignore

    def is_alive(self) -> bool:
        """Is the ZAP thread currently running?"""
        return bool(self.thread and self.thread.is_alive())

    def __del__(self) -> None:
        self.stop()


__all__ = ['ThreadAuthenticator']
