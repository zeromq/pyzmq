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

    pipe: zmq.asyncio.Socket
    loop: asyncio.AbstractEventLoop

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
                self.authenticator = None
            if self.pipe:
                self.pipe.close()
                self.pipe = None  # type: ignore

            loop.close()

    async def _run(self):
        aio_context = zmq.asyncio.Context.shadow(self.context.underlying)

        # create a socket to communicate back to main thread.
        self.pipe: "zmq.asyncio.Socket" = aio_context.socket(zmq.PAIR)
        self.pipe.linger = 1
        self.pipe.connect(self.endpoint)

        self.authenticator = AsyncioAuthenticator(
            aio_context, encoding=self.encoding, log=self.log
        )
        self.authenticator.start()

        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.pipe, zmq.POLLIN)
        self.started.set()

        while True:
            events = await self.poller.poll()
            if self.pipe in dict(events):
                msg = await self.pipe.recv_multipart()
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
                self.log.exception("Failed to allow %s", addresses)

        elif command == b'DENY':
            addresses = [m.decode(self.encoding) for m in msg[1:]]
            try:
                self.authenticator.deny(*addresses)
            except Exception:
                self.log.exception("Failed to deny %s", addresses)

        elif command == b'PLAIN':
            domain = msg[1].decode(self.encoding)
            json_passwords = msg[2]
            passwords: Dict[str, str] = cast(
                Dict[str, str], jsonapi.loads(json_passwords)
            )
            self.authenticator.configure_plain(domain, passwords)

        elif command == b'CURVE':
            # For now we don't do anything with domains
            domain = msg[1].decode(self.encoding)

            # If location is CURVE_ALLOW_ANY, allow all clients. Otherwise
            # treat location as a directory that holds the certificates.
            location = msg[2].decode(self.encoding)
            self.authenticator.configure_curve(domain, location)

        elif command == b'TERMINATE':
            return True

        else:
            self.log.error("Invalid auth command from API: %r", command)

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
        return getattr(self.thread.authenticator, key)

    def allow(self, *addresses: str):
        self.pipe.send_multipart(
            [b'ALLOW'] + [a.encode(self.encoding) for a in addresses]
        )

    def deny(self, *addresses: str):
        self.pipe.send_multipart(
            [b'DENY'] + [a.encode(self.encoding) for a in addresses]
        )

    def configure_plain(
        self, domain: str = '*', passwords: Optional[Dict[str, str]] = None
    ):
        self.pipe.send_multipart(
            [b'PLAIN', domain.encode(self.encoding), jsonapi.dumps(passwords or {})]
        )

    def configure_curve(self, domain: str = '*', location: str = ''):
        domain = domain.encode(self.encoding)
        location = location.encode(self.encoding)
        self.pipe.send_multipart([b'CURVE', domain, location])

    def configure_curve_callback(
        self, domain: str = '*', credentials_provider: Any = None
    ):
        self.thread.authenticator.configure_curve_callback(
            domain, credentials_provider=credentials_provider
        )

    def start(self) -> None:
        """Start the authentication thread"""
        # create a socket to communicate with auth thread.
        self.pipe = self.context.socket(zmq.PAIR)
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
