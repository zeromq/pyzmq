from __future__ import annotations

from typing import TYPE_CHECKING

from zmq.eventloop import zmqstream
from zmq.green.eventloop.ioloop import IOLoop

if TYPE_CHECKING:
    from zmq.sugar.socket import Socket


class ZMQStream(zmqstream.ZMQStream):
    def __init__(self, socket: Socket, io_loop: IOLoop | None = None) -> None:
        io_loop = io_loop or IOLoop.instance()
        super().__init__(socket, io_loop=io_loop)


__all__ = ["ZMQStream"]
