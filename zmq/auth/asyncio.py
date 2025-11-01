"""ZAP Authenticator integrated with the asyncio IO loop.

.. versionadded:: 15.2
"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import asyncio
import warnings
from typing import Any, Optional

import zmq
from zmq.asyncio import Poller

from .base import Authenticator


class AsyncioAuthenticator(Authenticator):
    """ZAP authentication for use in the asyncio IO loop

    .. versionadded:: 27.2
        Multiple authenticators can now run in the same process
        by specifying different socket addresses in ``start()``.
        See :class:`zmq.auth.Authenticator` for details and examples.
    """

    __poller: Optional[Poller]
    __task: Any

    def __init__(
        self,
        context: Optional["zmq.Context"] = None,
        loop: Any = None,
        encoding: str = 'utf-8',
        log: Any = None,
    ):
        super().__init__(context, encoding, log)
        if loop is not None:
            warnings.warn(
                f"{self.__class__.__name__}(loop) is deprecated and ignored",
                DeprecationWarning,
                stacklevel=2,
            )
        self.__poller = None
        self.__task = None

    async def __handle_zap(self) -> None:
        while self.__poller is not None:
            events = await self.__poller.poll()
            if self.zap_socket in dict(events):
                msg = self.zap_socket.recv_multipart()
                await self.handle_zap_message(msg)

    def start(self, socket_addr="inproc://zeromq.zap.01") -> None:
        """Start ZAP authentication

        Parameters
        ----------
        socket_addr : str, optional
            The address to bind the ZAP socket to.
            Default is "inproc://zeromq.zap.01"

            .. versionadded:: 27.2
                Support for custom socket addresses, enabling multiple
                authenticators in the same process.
        """
        super().start(socket_addr)
        self.__poller = Poller()
        self.__poller.register(self.zap_socket, zmq.POLLIN)
        self.__task = asyncio.ensure_future(self.__handle_zap())

    def stop(self) -> None:
        """Stop ZAP authentication"""
        if self.__task:
            self.__task.cancel()
        if self.__poller:
            self.__poller.unregister(self.zap_socket)
            self.__poller = None
        super().stop()


__all__ = ["AsyncioAuthenticator"]
