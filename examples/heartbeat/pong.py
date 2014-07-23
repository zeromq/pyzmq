#!/usr/bin/env python
"""This launches an echoing rep socket device using 
zmq.devices.ThreadDevice, and runs a blocking numpy action. 
The rep socket should remain responsive to pings during this time.

Use ping.py to see how responsive it is.

Authors
-------
* MinRK
"""
from __future__ import print_function

import time
import numpy
import zmq
from zmq import devices

ctx = zmq.Context()

dev = devices.ThreadDevice(zmq.FORWARDER, zmq.REP, -1)
dev.bind_in('tcp://127.0.0.1:10111')
dev.setsockopt_in(zmq.IDENTITY, b"whoda")
dev.start()

#wait for connections
time.sleep(1)

A = numpy.random.random((2**11,2**12))
print("starting blocking loop")
while True:
    tic = time.time()
    numpy.dot(A,A.transpose())
    print("blocked for %.3f s"%(time.time()-tic))
