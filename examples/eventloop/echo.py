#!/usr/bin/env python
"""A basic ZMQ echo server using the tornado eventloop

without relying on tornado integration (see echostream, echofuture).
"""

import zmq
from tornado import ioloop

def echo(sock, events):
    # We don't know how many recv's we can do?
    if not sock.EVENTS & zmq.POLLIN:
        # not a read event
        return
    msg = sock.recv_multipart()
    print(msg)
    sock.send_multipart(msg)
    # avoid starving due to edge-triggered event FD
    # if there is more than one read event waiting
    if sock.EVENTS & zmq.POLLIN:
        ioloop.IOLoop.current().add_callback(echo, sock, events)

ctx = zmq.Context.instance()
s = ctx.socket(zmq.ROUTER)
s.bind('tcp://127.0.0.1:5555')

loop = ioloop.IOLoop.current()
loop.add_handler(s, echo, loop.READ)
loop.start()
