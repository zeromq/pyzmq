#!/usr/bin/env python
"""Adapted echo.py to put the send in the event loop using a ZMQStream.
"""
from typing import List

from tornado import ioloop

import zmq
from zmq.eventloop import zmqstream

loop = ioloop.IOLoop.current()

ctx = zmq.Context()
s = ctx.socket(zmq.ROUTER)
s.bind('tcp://127.0.0.1:5555')
stream = zmqstream.ZMQStream(s)


def echo(msg: List[bytes]):
    print(" ".join(map(repr, msg)))
    stream.send_multipart(msg)


stream.on_recv(echo)

loop.start()
