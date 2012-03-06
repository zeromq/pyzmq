#-----------------------------------------------------------------------------
#  Copyright (c) 2010-2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import time
from unittest import TestCase

import zmq
from zmq import devices

from zmq.tests import BaseZMQTestCase, SkipTest

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
devices.ThreadMonitoredQueue.context_factory = zmq.Context

class TestMonitoredQueue(BaseZMQTestCase):
    sockets = []
    
    def build_device(self, mon_sub=b"", in_prefix=b'in', out_prefix=b'out'):
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
        self.device.start()
        time.sleep(.2)
        try:
            # this is currenlty necessary to ensure no dropped monitor messages
            # see LIBZMQ-248 for more info
            mon.recv_multipart(zmq.NOBLOCK)
        except zmq.ZMQError:
            pass
        self.sockets.extend([alice, bob, mon])
        return alice, bob, mon
        
    
    def teardown_device(self):
        for socket in self.sockets:
            socket.close()
            del socket
        del self.device
        
    def test_reply(self):
        alice, bob, mon = self.build_device()
        alices = b"hello bob".split()
        alice.send_multipart(alices)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices, bobs)
        bobs = b"hello alice".split()
        bob.send_multipart(bobs)
        alices = self.recv_multipart(alice)
        self.assertEquals(alices, bobs)
        self.teardown_device()
    
    def test_queue(self):
        alice, bob, mon = self.build_device()
        alices = b"hello bob".split()
        alice.send_multipart(alices)
        alices2 = b"hello again".split()
        alice.send_multipart(alices2)
        alices3 = b"hello again and again".split()
        alice.send_multipart(alices3)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices, bobs)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices2, bobs)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices3, bobs)
        bobs = b"hello alice".split()
        bob.send_multipart(bobs)
        alices = self.recv_multipart(alice)
        self.assertEquals(alices, bobs)
        self.teardown_device()
    
    def test_monitor(self):
        alice, bob, mon = self.build_device()
        alices = b"hello bob".split()
        alice.send_multipart(alices)
        alices2 = b"hello again".split()
        alice.send_multipart(alices2)
        alices3 = b"hello again and again".split()
        alice.send_multipart(alices3)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices, bobs)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'in']+bobs, mons)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices2, bobs)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices3, bobs)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'in']+alices2, mons)
        bobs = b"hello alice".split()
        bob.send_multipart(bobs)
        alices = self.recv_multipart(alice)
        self.assertEquals(alices, bobs)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'in']+alices3, mons)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'out']+bobs, mons)
        self.teardown_device()
    
    def test_prefix(self):
        alice, bob, mon = self.build_device(b"", b'foo', b'bar')
        alices = b"hello bob".split()
        alice.send_multipart(alices)
        alices2 = b"hello again".split()
        alice.send_multipart(alices2)
        alices3 = b"hello again and again".split()
        alice.send_multipart(alices3)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices, bobs)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'foo']+bobs, mons)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices2, bobs)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices3, bobs)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'foo']+alices2, mons)
        bobs = b"hello alice".split()
        bob.send_multipart(bobs)
        alices = self.recv_multipart(alice)
        self.assertEquals(alices, bobs)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'foo']+alices3, mons)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'bar']+bobs, mons)
        self.teardown_device()
    
    def test_monitor_subscribe(self):
        alice, bob, mon = self.build_device(b"out")
        alices = b"hello bob".split()
        alice.send_multipart(alices)
        alices2 = b"hello again".split()
        alice.send_multipart(alices2)
        alices3 = b"hello again and again".split()
        alice.send_multipart(alices3)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices, bobs)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices2, bobs)
        bobs = self.recv_multipart(bob)
        self.assertEquals(alices3, bobs)
        bobs = b"hello alice".split()
        bob.send_multipart(bobs)
        alices = self.recv_multipart(alice)
        self.assertEquals(alices, bobs)
        mons = self.recv_multipart(mon)
        self.assertEquals([b'out']+bobs, mons)
        self.teardown_device()
    
    def test_router_router(self):
        """test router-router MQ devices"""
        dev = devices.ThreadMonitoredQueue(zmq.ROUTER, zmq.ROUTER, zmq.PUB, b'in', b'out')
        dev.setsockopt_in(zmq.LINGER, 0)
        dev.setsockopt_out(zmq.LINGER, 0)
        dev.setsockopt_mon(zmq.LINGER, 0)
        
        binder = self.context.socket(zmq.DEALER)
        porta = binder.bind_to_random_port('tcp://127.0.0.1')
        portb = binder.bind_to_random_port('tcp://127.0.0.1')
        binder.close()
        time.sleep(0.1)
        a = self.context.socket(zmq.DEALER)
        a.identity = b'a'
        b = self.context.socket(zmq.DEALER)
        b.identity = b'b'
        
        a.connect('tcp://127.0.0.1:%i'%porta)
        dev.bind_in('tcp://127.0.0.1:%i'%porta)
        b.connect('tcp://127.0.0.1:%i'%portb)
        dev.bind_out('tcp://127.0.0.1:%i'%portb)
        dev.start()
        time.sleep(0.2)
        if zmq.zmq_version_info() >= (3,1,0):
            # flush erroneous poll state, due to LIBZMQ-280
            ping_msg = [ b'ping', b'pong' ]
            for s in (a,b):
                s.send_multipart(ping_msg)
                try:
                    s.recv(zmq.NOBLOCK)
                except zmq.ZMQError:
                    pass
        msg = [ b'hello', b'there' ]
        a.send_multipart([b'b']+msg)
        bmsg = self.recv_multipart(b)
        self.assertEquals(bmsg, [b'a']+msg)
        b.send_multipart(bmsg)
        amsg = self.recv_multipart(a)
        self.assertEquals(amsg, [b'b']+msg)
