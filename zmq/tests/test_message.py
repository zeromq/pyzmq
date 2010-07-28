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
from zmq.tests import PollZMQTestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestMessage(TestCase):

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

    def test_unicode(self):
        """Test the unicode representations of the Messages."""
        s = u'asdf'
        self.assertRaises(TypeError, zmq.Message, s)
        for i in range(16):
            s = (2**i)*u'§'
            m = zmq.Message(s.encode('utf8'))
            self.assertEquals(s, unicode(m))
    

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
            self.assertEquals(s, str(m))
            self.assertEquals(s, str(m2))
            self.assert_(s is str(m))
            self.assert_(s is str(m2))
            del m2
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
            self.assertEquals(s, str(m))
            self.assertEquals(s, str(m2))
            self.assert_(s is str(m))
            self.assert_(s is str(m2))
            del m
            self.assertEquals(grc(s), 4)
            del m2
            self.assertEquals(grc(s), 2)
            del s
    
    def test_buffer_in(self):
        """test using a buffer as input"""
        ins = unicode("§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√",encoding='utf16')
        m = zmq.Message(buffer(ins))
        # outs = unicode(m.buffer,'utf16')
        # self.assertEquals(ins,outs)
        
    def test_buffer_out(self):
        """receiving buffered output"""
        ins = unicode("§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√",encoding='utf8')
        m = zmq.Message(ins.encode('utf8'))
        outb = m.buffer
        self.assertTrue(isinstance(outb, buffer))
        self.assert_(outb is m.buffer)
        self.assert_(m.buffer is m.buffer)
    
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
        

