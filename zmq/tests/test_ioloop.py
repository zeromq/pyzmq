#
#    Copyright (c) 2010 Min Ragan-Kelley
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import time
import os
import threading

import zmq
from zmq.tests import BaseZMQTestCase
from zmq.eventloop import ioloop
from zmq.utils.strtypes import asbytes as b

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
def printer():
    os.system("say hello")
    raise Exception
    print (time.time())

class Delay(threading.Thread):
    def __init__(self, f, delay=1):
        self.f=f
        self.delay=delay
        self.aborted=False
        self.cond=threading.Condition()
        super(Delay, self).__init__()
    
    def run(self):
        self.cond.acquire()
        self.cond.wait(self.delay)
        self.cond.release()
        if not self.aborted:
            self.f()
    
    def abort(self):
        self.aborted=True
        self.cond.acquire()
        self.cond.notify()
        self.cond.release()

class TestIOLoop(BaseZMQTestCase):

    def test_simple(self):
        """simple IOLoop creation test"""
        loop = ioloop.IOLoop()
        dc = ioloop.DelayedCallback(loop.stop, 200, loop)
        pc = ioloop.DelayedCallback(lambda : None, 10, loop)
        pc.start()
        dc.start()
        t = Delay(loop.stop,1)
        t.start()
        loop.start()
        if t.isAlive():
            t.abort()
        else:
            self.fail("IOLoop failed to exit")
    
    def test_timeout_compare(self):
        """test timeout comparisons"""
        t = ioloop._Timeout(1,2)
        t2 = ioloop._Timeout(1,3)
        self.assertEquals(t < t2, id(t) < id(t2))
        t2 = ioloop._Timeout(2,1)
        self.assertTrue(t < t2)

    def test_poller_events(self):
        """Tornado poller implementation maps events correctly"""
        req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        poller = ioloop.ZMQPoller()
        poller.register(req, ioloop.IOLoop.READ)
        poller.register(rep, ioloop.IOLoop.READ)
        events = dict(poller.poll(0))
        self.assertEquals(events.get(rep), None)
        self.assertEquals(events.get(req), None)
        
        poller.register(req, ioloop.IOLoop.WRITE)
        poller.register(rep, ioloop.IOLoop.WRITE)
        events = dict(poller.poll(1))
        self.assertEquals(events.get(req), ioloop.IOLoop.WRITE)
        self.assertEquals(events.get(rep), None)
        
        poller.register(rep, ioloop.IOLoop.READ)
        req.send(b('hi'))
        events = dict(poller.poll(1))
        self.assertEquals(events.get(rep), ioloop.IOLoop.READ)
        self.assertEquals(events.get(req), None)

