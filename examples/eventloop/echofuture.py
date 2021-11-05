#!/usr/bin/env python
"""A basic ZMQ echo server with zmq.eventloop.future"""

from tornado import ioloop

import zmq
from zmq.eventloop.future import Context


async def echo(sock):
    while True:
        msg = await sock.recv_multipart()
        await sock.send_multipart(msg)


ctx = Context.instance()
s = ctx.socket(zmq.ROUTER)
s.bind('tcp://127.0.0.1:5555')

loop = ioloop.IOLoop.current()
loop.spawn_callback(echo, s)
loop.start()
