#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#    Copyright (c) 2010 Brian E. Granger
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

import copy
import sys
from sys import getrefcount as grc
import time
from pprint import pprint
from unittest import TestCase

import zmq
from zmq.tests import BaseZMQTestCase, SkipTest
from zmq.utils.strtypes import unicode,bytes

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

# some useful constants:

x = 'x'.encode()

try:
    view = memoryview
except NameError:
    view = buffer

rc0 = grc(x)
v = view(x)
view_rc = grc(x) - rc0

class TestMessage(BaseZMQTestCase):

    def test_above_30(self):
        """Message above 30 bytes are never copied by 0MQ."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*x
            self.assertEquals(grc(s), 2)
            m = zmq.Message(s)
            self.assertEquals(grc(s), 4)
            del m
            self.assertEquals(grc(s), 2)
            del s

    def test_str(self):
        """Test the str representations of the Messages."""
        for i in range(16):
            s = (2**i)*x
            m = zmq.Message(s)
            self.assertEquals(s, str(m).encode())

    def test_bytes(self):
        """Test the Message.bytes property."""
        for i in range(1,16):
            s = (2**i)*x
            m = zmq.Message(s)
            b = m.bytes
            self.assertEquals(s, m.bytes)
            # check that it copies
            self.assert_(b is not s)
            # check that it copies only once
            self.assert_(b is m.bytes)

    def test_unicode(self):
        """Test the unicode representations of the Messages."""
        s = unicode('asdf')
        self.assertRaises(TypeError, zmq.Message, s)
        u = '§'
        if str is not unicode:
            u = u.decode('utf8')
        for i in range(16):
            s = (2**i)*u
            m = zmq.Message(s.encode('utf8'))
            self.assertEquals(s, unicode(m.bytes,'utf8'))

    def test_len(self):
        """Test the len of the Messages."""
        for i in range(16):
            s = (2**i)*x
            m = zmq.Message(s)
            self.assertEquals(len(s), len(m))

    def test_lifecycle1(self):
        """Run through a ref counting cycle with a copy."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*x
            rc = 2
            self.assertEquals(grc(s), rc)
            m = zmq.Message(s)
            rc += 2
            self.assertEquals(grc(s), rc)
            m2 = copy.copy(m)
            rc += 1
            self.assertEquals(grc(s), rc)
            b = m2.buffer

            rc += view_rc
            self.assertEquals(grc(s), rc)

            self.assertEquals(s, str(m).encode())
            self.assertEquals(s, str(m2).encode())
            self.assertEquals(s, m.bytes)
            # self.assert_(s is str(m))
            # self.assert_(s is str(m2))
            del m2
            rc -= 1
            self.assertEquals(grc(s), rc)
            rc -= view_rc
            del b
            self.assertEquals(grc(s), rc)
            del m
            rc -= 2
            self.assertEquals(grc(s), rc)
            self.assertEquals(rc, 2)
            del s

    def test_lifecycle2(self):
        """Run through a different ref counting cycle with a copy."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*x
            rc = 2
            self.assertEquals(grc(s), rc)
            m = zmq.Message(s)
            rc += 2
            self.assertEquals(grc(s), rc)
            m2 = copy.copy(m)
            rc += 1
            self.assertEquals(grc(s), rc)
            b = m.buffer
            rc += view_rc
            self.assertEquals(grc(s), rc)
            self.assertEquals(s, str(m).encode())
            self.assertEquals(s, str(m2).encode())
            self.assertEquals(s, m2.bytes)
            self.assertEquals(s, m.bytes)
            # self.assert_(s is str(m))
            # self.assert_(s is str(m2))
            del b
            self.assertEquals(grc(s), rc)
            del m
            # m.buffer is kept until m is del'd
            rc -= view_rc
            rc -= 1
            self.assertEquals(grc(s), rc)
            del m2
            rc -= 2
            self.assertEquals(grc(s), rc)
            self.assertEquals(rc, 2)
            del s
    
    def test_tracker(self):
        m = zmq.Message('asdf'.encode(), track=True)
        self.assertFalse(m.done)
        pm = zmq.MessageTracker(m)
        self.assertFalse(pm.done)
        del m
        self.assertTrue(pm.done)
    
    def test_no_tracker(self):
        m = zmq.Message('asdf'.encode(), track=False)
        self.assertRaises(ValueError, getattr, m, 'done')
        m2 = copy.copy(m)
        self.assertRaises(ValueError, getattr, m2, 'done')
        self.assertRaises(ValueError, zmq.MessageTracker, m)
    
    def test_multi_tracker(self):
        m = zmq.Message('asdf'.encode(), track=True)
        m2 = zmq.Message('whoda'.encode(), track=True)
        mt = zmq.MessageTracker(m,m2)
        self.assertFalse(m.done)
        self.assertFalse(mt.done)
        self.assertRaises(zmq.NotDone, mt.wait, 0.1)
        del m
        time.sleep(0.1)
        self.assertRaises(zmq.NotDone, mt.wait, 0.1)
        self.assertFalse(mt.done)
        del m2
        self.assertTrue(mt.wait() is None)
        self.assertTrue(mt.done)
        
    
    def test_buffer_in(self):
        """test using a buffer as input"""
        if unicode is str:
            ins = "§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√".encode('utf8')
        else:
            ins = "§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√"
        m = zmq.Message(view(ins))
    
    def test_bad_buffer_in(self):
        """test using a bad object"""
        self.assertRaises(TypeError, zmq.Message, 5)
        self.assertRaises(TypeError, zmq.Message, object())
        
    def test_buffer_out(self):
        """receiving buffered output"""
        if unicode is str:
            ins = "§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√".encode('utf8')
        else:
            ins = "§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√"
        m = zmq.Message(ins)
        outb = m.buffer
        self.assertTrue(isinstance(outb, view))
        self.assert_(outb is m.buffer)
        self.assert_(m.buffer is m.buffer)
    
    def test_multisend(self):
        """ensure that a message remains intact after multiple sends"""
        a,b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        s = "message".encode()
        m = zmq.Message(s)
        self.assertEquals(s, m.bytes)
        
        a.send(m, copy=False)
        time.sleep(0.1)
        self.assertEquals(s, m.bytes)
        a.send(m, copy=False)
        time.sleep(0.1)
        self.assertEquals(s, m.bytes)
        a.send(m, copy=True)
        time.sleep(0.1)
        self.assertEquals(s, m.bytes)
        a.send(m, copy=True)
        time.sleep(0.1)
        self.assertEquals(s, m.bytes)
        for i in range(4):
            r = b.recv()
            self.assertEquals(s,r)
        self.assertEquals(s, m.bytes)
    
    def test_buffer_numpy(self):
        """test non-copying numpy array messages"""
        try:
            import numpy
        except ImportError:
            raise SkipTest
        shapes = map(numpy.random.randint, [2]*5,[16]*5)
        for i in range(1,len(shapes)+1):
            shape = shapes[:i]
            A = numpy.random.random(shape)
            m = zmq.Message(A)
            self.assertEquals(A.data, m.buffer)
            B = numpy.frombuffer(m.buffer,dtype=A.dtype).reshape(A.shape)
            self.assertEquals((A==B).all(), True)
    
    def test_memoryview(self):
        """test messages from memoryview (only valid for python >= 2.7)"""
        major,minor = sys.version_info[:2]
        if not (major >= 3 or (major == 2 and minor >= 7)):
            raise SkipTest

        s = 'carrotjuice'.encode()
        v = memoryview(s)
        m = zmq.Message(s)
        buf = m.buffer
        s2 = buf.tobytes()
        self.assertEquals(s2,s)
        self.assertEquals(m.bytes,s)
        

