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
from sys import getrefcount as grc
import time
from unittest import TestCase

import zmq
from zmq.tests import BaseZMQTestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestMessage(BaseZMQTestCase):

    def test_above_30(self):
        """Message above 30 bytes are never copied by 0MQ."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*'x'
            self.assertEquals(grc(s), 2)
            m = zmq.Message(s)
            self.assertEquals(grc(s), 4)
            del m
            self.assertEquals(grc(s), 2)
            del s

    def test_str(self):
        """Test the str representations of the Messages."""
        for i in range(16):
            s = (2**i)*'x'
            m = zmq.Message(s)
            self.assertEquals(s, str(m))
            self.assert_(s is str(m))

    def test_bytes(self):
        """Test the Message.bytes property."""
        for i in range(1,16):
            s = (2**i)*'x'
            m = zmq.Message(s)
            b = m.bytes
            self.assertEquals(s, m.bytes)
            # check that it copies
            self.assert_(b is not s)
            # check that it copies only once
            self.assert_(b is m.bytes)

    def test_unicode(self):
        """Test the unicode representations of the Messages."""
        s = u'asdf'
        self.assertRaises(TypeError, zmq.Message, s)
        for i in range(16):
            s = (2**i)*u'§'
            m = zmq.Message(s.encode('utf8'))
            self.assertEquals(s, unicode(str(m),'utf8'))
    

    def test_len(self):
        """Test the len of the Messages."""
        for i in range(16):
            s = (2**i)*'x'
            m = zmq.Message(s)
            self.assertEquals(len(s), len(s))

    def test_lifecycle1(self):
        """Run through a ref counting cycle with a copy."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*'x'
            self.assertEquals(grc(s), 2)
            m = zmq.Message(s)
            self.assertEquals(grc(s), 4)
            m2 = copy.copy(m)
            self.assertEquals(grc(s), 5)
            b = m2.buffer
            self.assertEquals(grc(s), 6)
            self.assertEquals(s, str(m))
            self.assertEquals(s, str(m2))
            self.assertEquals(s, m.bytes)
            self.assert_(s is str(m))
            self.assert_(s is str(m2))
            del m2
            self.assertEquals(grc(s), 5)
            del b
            self.assertEquals(grc(s), 4)
            del m
            self.assertEquals(grc(s), 2)
            del s

    def test_lifecycle2(self):
        """Run through a different ref counting cycle with a copy."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*'x'
            self.assertEquals(grc(s), 2)
            m = zmq.Message(s)
            self.assertEquals(grc(s), 4)
            m2 = copy.copy(m)
            self.assertEquals(grc(s), 5)
            b = m.buffer
            self.assertEquals(grc(s), 6)
            self.assertEquals(s, str(m))
            self.assertEquals(s, str(m2))
            self.assertEquals(s, m2.bytes)
            self.assertEquals(s, m.bytes)
            self.assert_(s is str(m))
            self.assert_(s is str(m2))
            del b
            self.assertEquals(grc(s), 6)
            del m
            self.assertEquals(grc(s), 4)
            del m2
            self.assertEquals(grc(s), 2)
            del s
    
    def test_tracker(self):
        m = zmq.Message('asdf')
        self.assertFalse(m.done)
        pm = zmq.MessageTracker(m)
        self.assertFalse(pm.done)
        del m
        self.assertTrue(pm.done)
    
    def test_multi_tracker(self):
        m = zmq.Message('asdf')
        m2 = zmq.Message('whoda')
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
        ins = unicode("§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√",encoding='utf16')
        m = zmq.Message(buffer(ins))
    
    def test_bad_buffer_in(self):
        """test using a bad object"""
        self.assertRaises(TypeError, zmq.Message, 5)
        self.assertRaises(TypeError, zmq.Message, object())
        
    def test_buffer_out(self):
        """receiving buffered output"""
        ins = unicode("§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√",encoding='utf8')
        m = zmq.Message(ins.encode('utf8'))
        outb = m.buffer
        self.assertTrue(isinstance(outb, buffer))
        self.assert_(outb is m.buffer)
        self.assert_(m.buffer is m.buffer)
    
    def test_multisend(self):
        """ensure that a message remains intact after multiple sends"""
        a,b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        s = "message"
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
            return
        shapes = map(numpy.random.randint, [2]*5,[16]*5)
        for i in range(1,len(shapes)+1):
            shape = shapes[:i]
            A = numpy.random.random(shape)
            m = zmq.Message(A)
            self.assertEquals(A.data, m.buffer)
            B = numpy.frombuffer(m.buffer,dtype=A.dtype).reshape(A.shape)
            self.assertEquals((A==B).all(), True)
        

