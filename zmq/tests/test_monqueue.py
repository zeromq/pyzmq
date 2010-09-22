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
from unittest import TestCase

import zmq
from zmq import devices
from zmq.tests import BaseZMQTestCase


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestMonitoredQueue(BaseZMQTestCase):
    sockets = []
    pass
    
    def build_device(self, mon_sub="", in_prefix='in', out_prefix='out'):
        self.device = devices.ThreadMonitoredQueue(zmq.PAIR, zmq.PAIR, zmq.PUB,
                                            in_prefix, out_prefix)
        alice = self.context.socket(zmq.PAIR)
        bob = self.context.socket(zmq.PAIR)
        mon = self.context.socket(zmq.SUB)
        
        aport = alice.bind_to_random_port('tcp://127.0.0.1')
        bport = bob.bind_to_random_port('tcp://127.0.0.1')
        mport = mon.bind_to_random_port('tcp://127.0.0.1')
        mon.setsockopt(zmq.SUBSCRIBE, mon_sub)
        
        self.device.connect_in("tcp://127.0.0.1:%i"%aport)
        self.device.connect_out("tcp://127.0.0.1:%i"%bport)
        self.device.connect_mon("tcp://127.0.0.1:%i"%mport)
        time.sleep(.2)
        self.device.start()
        self.sockets.extend([alice, bob, mon])
        return alice, bob, mon
        
    
    def teardown_device(self):
        for socket in self.sockets:
            socket.close()
            del socket
        del self.device
        
    def test_reply(self):
        alice, bob, mon = self.build_device("")
        alices = "hello bob".split()
        alice.send_multipart(alices)
        bobs = bob.recv_multipart()
        self.assertEquals(alices, bobs)
        bobs = "hello alice".split()
        bob.send_multipart(bobs)
        alices = alice.recv_multipart()
        self.assertEquals(alices, bobs)
        self.teardown_device()
    
    def test_queue(self):
        alice, bob, mon = self.build_device("")
        alices = "hello bob".split()
        alice.send_multipart(alices)
        alices2 = "hello again".split()
        alice.send_multipart(alices2)
        alices3 = "hello again and again".split()
        alice.send_multipart(alices3)
        bobs = bob.recv_multipart()
        self.assertEquals(alices, bobs)
        bobs = bob.recv_multipart()
        self.assertEquals(alices2, bobs)
        bobs = bob.recv_multipart()
        self.assertEquals(alices3, bobs)
        bobs = "hello alice".split()
        bob.send_multipart(bobs)
        alices = alice.recv_multipart()
        self.assertEquals(alices, bobs)
        self.teardown_device()
    
    def test_monitor(self):
        alice, bob, mon = self.build_device("")
        alices = "hello bob".split()
        alice.send_multipart(alices)
        alices2 = "hello again".split()
        alice.send_multipart(alices2)
        alices3 = "hello again and again".split()
        alice.send_multipart(alices3)
        bobs = bob.recv_multipart()
        self.assertEquals(alices, bobs)
        mons = mon.recv_multipart()
        self.assertEquals(['in']+bobs, mons)
        bobs = bob.recv_multipart()
        self.assertEquals(alices2, bobs)
        bobs = bob.recv_multipart()
        self.assertEquals(alices3, bobs)
        mons = mon.recv_multipart()
        self.assertEquals(['in']+alices2, mons)
        bobs = "hello alice".split()
        bob.send_multipart(bobs)
        alices = alice.recv_multipart()
        self.assertEquals(alices, bobs)
        mons = mon.recv_multipart()
        self.assertEquals(['in']+alices3, mons)
        mons = mon.recv_multipart()
        self.assertEquals(['out']+bobs, mons)
        self.teardown_device()
    
    def test_prefix(self):
        alice, bob, mon = self.build_device("", 'foo', 'bar')
        alices = "hello bob".split()
        alice.send_multipart(alices)
        alices2 = "hello again".split()
        alice.send_multipart(alices2)
        alices3 = "hello again and again".split()
        alice.send_multipart(alices3)
        bobs = bob.recv_multipart()
        self.assertEquals(alices, bobs)
        mons = mon.recv_multipart()
        self.assertEquals(['foo']+bobs, mons)
        bobs = bob.recv_multipart()
        self.assertEquals(alices2, bobs)
        bobs = bob.recv_multipart()
        self.assertEquals(alices3, bobs)
        mons = mon.recv_multipart()
        self.assertEquals(['foo']+alices2, mons)
        bobs = "hello alice".split()
        bob.send_multipart(bobs)
        alices = alice.recv_multipart()
        self.assertEquals(alices, bobs)
        mons = mon.recv_multipart()
        self.assertEquals(['foo']+alices3, mons)
        mons = mon.recv_multipart()
        self.assertEquals(['bar']+bobs, mons)
        self.teardown_device()
    
    def test_monitor_subscribe(self):
        alice, bob, mon = self.build_device("out")
        alices = "hello bob".split()
        alice.send_multipart(alices)
        alices2 = "hello again".split()
        alice.send_multipart(alices2)
        alices3 = "hello again and again".split()
        alice.send_multipart(alices3)
        bobs = bob.recv_multipart()
        self.assertEquals(alices, bobs)
        bobs = bob.recv_multipart()
        self.assertEquals(alices2, bobs)
        bobs = bob.recv_multipart()
        self.assertEquals(alices3, bobs)
        bobs = "hello alice".split()
        bob.send_multipart(bobs)
        alices = alice.recv_multipart()
        self.assertEquals(alices, bobs)
        mons = mon.recv_multipart()
        self.assertEquals(['out']+bobs, mons)
        self.teardown_device()
    
