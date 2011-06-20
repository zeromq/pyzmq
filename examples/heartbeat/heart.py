#!/usr/bin/env python
"""This launches an echoing rep socket device,
and runs a blocking numpy action. The rep socket should
remain responsive to pings during this time. Use heartbeater.py to
ping this heart, and see the responsiveness.

Authors
-------
* MinRK
"""

import time
import numpy
import zmq
from zmq import devices

ctx = zmq.Context()

dev = devices.ThreadDevice(zmq.FORWARDER, zmq.SUB, zmq.DEALER)
dev.setsockopt_in(zmq.SUBSCRIBE, "")
dev.connect_in('tcp://127.0.0.1:5555')
dev.connect_out('tcp://127.0.0.1:5556')
dev.start()

#wait for connections
time.sleep(1)

A = numpy.random.random((2**11,2**11))
print "starting blocking loop"
while True:
    tic = time.time()
    numpy.dot(A,A.transpose())
    print "blocked for %.3f s"%(time.time()-tic)

