#!/usr/bin/env python
"""A basic ZMQ echo server with zmq.eventloop.future"""

import zmq
from tornado import gen, ioloop
from zmq.eventloop.future import Context

@gen.coroutine
def echo(sock):
    while True:
        msg = yield sock.recv_multipart()
        yield sock.send_multipart(msg)

ctx = Context.instance()
s = ctx.socket(zmq.ROUTER)
s.bind('tcp://127.0.0.1:5555')

loop = ioloop.IOLoop.current()
loop.spawn_callback(echo, s)
loop.start()
