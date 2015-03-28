#!/usr/bin/env python

'''
No protection at all.

All connections are accepted, there is no authentication, and no privacy. 

This is how ZeroMQ always worked until we built security into the wire 
protocol in early 2013. Internally, it uses a security mechanism called 
"NULL".

Author: Chris Laws
'''

import zmq


ctx = zmq.Context.instance()

server = ctx.socket(zmq.PUSH)
server.bind('tcp://*:9000')

client = ctx.socket(zmq.PULL)
client.connect('tcp://127.0.0.1:9000')

server.send(b"Hello")
msg = client.recv()
if msg == b"Hello":
    print("Grasslands test OK")
