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
            self.assert_(False, "IOLoop failed to exit")
    
    def test_timeout_compare(self):
        """test timeout comparisons"""
        t = ioloop._Timeout(1,2)
        t2 = ioloop._Timeout(1,3)
        self.assertEquals(t < t2, id(2) < id(3))
        t2 = ioloop._Timeout(1,2)
        self.assertFalse(t < t2)
        t2 = ioloop._Timeout(2,1)
        self.assertTrue(t < t2)
