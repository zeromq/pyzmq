"""Garbage collection thread for representing zmq refcount of Python objects
used in zero-copy sends.
"""

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

import atexit
import struct

from os import getpid
from collections import namedtuple
from threading import Thread, Event, Lock

import zmq

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

gcref = namedtuple('gcref', ['obj', 'event'])

class GarbageCollectorThread(Thread):
    """Thread in which garbage collection actually happens."""
    def __init__(self, gc):
        super(GarbageCollectorThread, self).__init__()
        self.gc = gc
        self.daemon = True
        self.pid = getpid()
        self.ready = Event()
    
    def run(self):
        s = self.gc.context.socket(zmq.PULL)
        s.linger = 0
        s.bind(self.gc.url)
        self.ready.set()
        
        while True:
            # detect fork
            if getpid is None or getpid() != self.pid:
                return
            msg = s.recv()
            if msg == b'DIE':
                break
            fmt = 'L' if len(msg) == 4 else 'Q'
            key = struct.unpack(fmt, msg)[0]
            tup = self.gc.refs.pop(key, None)
            if tup and tup.event:
                tup.event.set()
            del tup
        s.close()


class GarbageCollector(object):
    """PyZMQ Garbage Collector
    
    Used for representing the reference held by libzmq during zero-copy sends.
    This object holds a dictionary, keyed by Python id,
    of the Python objects whose memory are currently in use by zeromq.
    
    When zeromq is done with the memory, it sends a message on an inproc PUSH socket
    containing the packed size_t (32 or 64-bit unsigned int),
    which is the key in the dict.
    When the PULL socket in the gc thread receives that message,
    the reference is popped from the dict,
    and any tracker events that should be signaled fire.
    """
    
    context = None
    refs = None
    _finished = False
    _lock = None
    url = "inproc://pyzmq.gc.01"
    
    def __init__(self):
        super(GarbageCollector, self).__init__()
        self.refs = {}
        self.pid = None
        self.thread = None
        self.context = None
        self._lock = Lock()
        atexit.register(self.stop)
    
    def stop(self):
        """stop the garbage-collection thread"""
        if not self.is_alive():
            return
        push = self.context.socket(zmq.PUSH)
        push.connect(self.url)
        push.send(b'DIE')
        push.close()
        self.thread.join()
        self.context.term()
        self.refs.clear()
    
    def start(self):
        """Start a new garbage collection thread.
        
        Creates a new zmq Context used for garbage collection.
        Under most circumstances, this will only be called once per process.
        """
        self.pid = getpid()
        self.context = zmq.Context()
        self.refs = {}
        self.thread = GarbageCollectorThread(self)
        self.thread.start()
        self.thread.ready.wait()
    
    def is_alive(self):
        """Is the garbage collection thread currently running?
        
        Includes checks for process shutdown or fork.
        """
        if (getpid is None or
            getpid() != self.pid or
            self.thread is None or
            not self.thread.is_alive()
            ):
            return False
        return True
    
    def store(self, obj, event=None):
        """store an object and (optionally) event for zero-copy"""
        if not self.is_alive():
            # safely start the gc thread
            # use lock and double check,
            # so we don't start multiple threads
            with self._lock:
                if not self.is_alive():
                    self.start()
        tup = gcref(obj, event)
        theid = id(tup)
        self.refs[theid] = tup
        return theid
    
    def __del__(self):
        if not self.is_alive():
            return
        try:
            self.stop()
        except Exception as e:
            raise (e)

gc = GarbageCollector()
