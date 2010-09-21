#!/usr/bin/env python
"""For use with pong.py

This script simply pings a process started by pong.py or tspong.py, to 
demonstrate that zmq remains responsive while Python blocks.

Authors
-------
* MinRK
"""

import time
import numpy
import zmq

ctx = zmq.Context()

req = ctx.socket(zmq.REQ)
req.connect('tcp://127.0.0.1:10111')

#wait for connects
time.sleep(1)
n=0
while True:
    time.sleep(numpy.random.random())
    for i in range(4):
        n+=1
        msg = 'ping %i'%n
        tic = time.time()
        req.send(msg)
        resp = req.recv()
        print "%s: %.2f ms" % (msg, 1000*(time.time()-tic))
        assert msg == resp

