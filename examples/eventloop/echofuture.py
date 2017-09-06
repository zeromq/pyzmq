#!/usr/bin/env python
"""A basic ZMQ echo server with zmq.eventloop.future"""

import zmq
from tornado import gen, ioloop
from zmq.eventloop.future import Context

@gen.coroutine
def echo(sock, events):
    while True:
        msg = yield s.recv_multipart()
        yield s.send_multipart()

ctx = Context.instance()
s = ctx.socket(zmq.ROUTER)
s.bind('tcp://127.0.0.1:5555')

loop = ioloop.IOLoop.current()
loop.spawn_callback(echo)
loop.start()
