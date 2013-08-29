"""Garbage collection thread for zero-copy"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Brian E. Granger & Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import struct

from os import getpid
from collections import namedtuple
from threading import Thread

import zmq

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

gcref = namedtuple('gcref', ['obj', 'event'])

class GarbageCollector(Thread):
    """Garbage Collector Thread
    
    Used for representing the reference held by libzmq during zero-copy sends.
    This object holds a dictionary, keyed by Python id,
    of the Python objects whose memory are currently in use by zeromq.
    
    When zeromq is done with the memory, it sends a message on an inproc PULL socket
    containing the packed size_t (32 or 64-bit unsigned int),
    which is the key in the dict.
    When this Thread receives that message, the reference is popped from the dict,
    and any tracker events that should be signaled fire.
    """
    
    context = None
    refs = None
    url = "inproc://pyzmq.gc.01"
    
    def __init__(self):
        super(GarbageCollector, self).__init__()
        self.context = zmq.Context()
        self.refs = {}
        self.daemon = True
        self.pid = getpid()
    
    def run(self):
        s = self.context.socket(zmq.PULL)
        s.bind(self.url)
        
        while True:
            msg = s.recv()
            if msg == b'DIE':
                break
            fmt = 'L' if len(msg) == 4 else 'Q'
            key = struct.unpack(fmt, msg)[0]
            tup = self.refs.pop(key)
            if tup.event:
                tup.event.set()
            del tup
        self.refs.clear()
        s.close(linger=0)
        self.context.term()
    
    def stop(self):
        """stop the garbage-collection thread"""
        push = self.context.socket(zmq.PUSH)
        push.connect(self.url)
        push.send(b'DIE')
        push.close()
        self.context.term()
    
    def store(self, object, event=None):
        """store an object and (optionally) event for zero-copy"""
        if not self.is_alive():
            self.start()
        tup = gcref(object, event)
        theid = id(tup)
        self.refs[theid] = tup
        return theid
    
    def __del__(self):
        if getpid() != self.pid:
            return
        self.stop()

gc = GarbageCollector()
