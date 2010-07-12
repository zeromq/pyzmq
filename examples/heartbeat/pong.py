#!/usr/bin/env python
import time
import numpy
import zmq

ctx = zmq.Context()

rep = ctx.socket(zmq.REP)
rep.bind('tcp://127.0.0.1:10111')

#wait for connections
time.sleep(1)

dev = zmq.Device(zmq.FORWARDER, rep, rep)

A = numpy.random.random((2**11,2**12))
while True:
    tic = time.time()
    numpy.dot(A,A.transpose())
    print "blocked for %.3f s"%(time.time()-tic)

