#!/usr/bin/env python
"""A trivial ZMQ echo server using the eventloop.

Authors
-------
* MinRK
"""

import zmq
from zmq.eventloop import ioloop

loop = ioloop.IOLoop.instance()

ctx = zmq.Context()
s = ctx.socket(zmq.REP)
s.bind('tcp://127.0.0.1:5555')

def rep_handler(sock, events):
    # We don't know how many recv's we can do?
    msg = sock.recv()
    # No guarantee that we can do the send. We need a way of putting the
    # send in the event loop.
    sock.send(msg)

loop.add_handler(s, rep_handler, zmq.POLLIN)

loop.start()