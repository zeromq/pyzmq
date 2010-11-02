#!/usr/bin/env python
from Crypto.Cipher import Blowfish
import base64
import os
import time
import math

import zmq

from zmq.crypto import EncryptedSocket

# the block size for the cipher object; must be 16, 24, or 32 for AES, or just 8 for Blowfish.
BLOCK_SIZE = 8


# generate a random string, but in more legible base64
rands = lambda n: base64.b64encode(os.urandom(int(math.ceil(0.75*n))),'-_')[:n]

def echo(s1, s2, m, validate=False):
    """echo a message back and forth between two sockets, optionally
    checking that the result is the same as the input"""
    s1.send(m)
    m2 = s2.recv()
    s2.send(m2)
    m3 = s1.recv()
    if validate:
        assert m3 == m
    return m3

def runtest(nmsgs, msgsize, validate=False):
    """Run a test to see how much slower the EncryptedSocket is, compared
    to copying sends.  Input is the number of messages to use for the test,
    and msgsize is the length of the messages.  Random messages will
    be generated."""
    # generate random password.  This could be any string (block lenght requirements)
    secret = rands(BLOCK_SIZE)
    # create a Blowfish cipher:
    cipher = Blowfish.new(secret)
    
    ctx = zmq.Context()
    s1 = ctx.socket(zmq.REQ)
    port = s1.bind_to_random_port('tcp://127.0.0.1')
    s2 = ctx.socket(zmq.REP)
    s2.connect('tcp://127.0.0.1:%i'%port)
    # pass the cipher to EncryptedSockets. pad must be 8 for blowfish
    es1 = EncryptedSocket(ctx, zmq.REQ, cipher, pad=BLOCK_SIZE)
    es2 = EncryptedSocket(ctx, zmq.REP, cipher, pad=BLOCK_SIZE)
    port = es1.bind_to_random_port('tcp://127.0.0.1')
    es2.connect('tcp://127.0.0.1:%i'%port)
    
    msgs = [ rands(msgsize) for i in range(nmsgs) ]
    
    tic = time.time()
    for m in msgs:
        echo(s1,s2,m, validate)
    lap = time.time()
    for m in msgs:
        echo(es1,es2,m, validate)
    toc = time.time()
    
    s1.close()
    s2.close()
    es1.close()
    es2.close()
    ctx.term()
    
    t1 = lap-tic
    t2 = toc-lap
    
    return t2/t1



