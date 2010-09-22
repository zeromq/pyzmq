#!/usr/bin/env python
"""Adapted echo.py to put the send in the event loop using a ZMQStream.

Authors
-------
* MinRK
"""

import zmq
from zmq.eventloop import ioloop, zmqstream
loop = ioloop.IOLoop.instance()

ctx = zmq.Context()
s = ctx.socket(zmq.REP)
s.bind('tcp://127.0.0.1:5555')
stream = zmqstream.ZMQStream(s, loop)

def echo(msg):
    print " ".join(msg)
    stream.send_multipart(msg)

stream.on_recv(echo)

loop.start()