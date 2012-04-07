# -*- coding: utf8 -*-
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

import copy
import sys
from sys import getrefcount as grc
import time
from pprint import pprint
from unittest import TestCase

import zmq
from zmq.tests import BaseZMQTestCase, SkipTest
from zmq.utils.strtypes import unicode, bytes, asbytes, b
from zmq.utils.rebuffer import array_from_buffer

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

# some useful constants:

x = b'x'

try:
    view = memoryview
except NameError:
    view = buffer

rc0 = grc(x)
v = view(x)
view_rc = grc(x) - rc0

class TestFrame(BaseZMQTestCase):

    def test_above_30(self):
        """Message above 30 bytes are never copied by 0MQ."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*x
            self.assertEquals(grc(s), 2)
            m = zmq.Frame(s)
            self.assertEquals(grc(s), 4)
            del m
            self.assertEquals(grc(s), 2)
            del s

    def test_str(self):
        """Test the str representations of the Frames."""
        for i in range(16):
            s = (2**i)*x
            m = zmq.Frame(s)
            self.assertEquals(s, asbytes(m))

    def test_bytes(self):
        """Test the Frame.bytes property."""
        for i in range(1,16):
            s = (2**i)*x
            m = zmq.Frame(s)
            b = m.bytes
            self.assertEquals(s, m.bytes)
            # check that it copies
            self.assert_(b is not s)
            # check that it copies only once
            self.assert_(b is m.bytes)

    def test_unicode(self):
        """Test the unicode representations of the Frames."""
        s = unicode('asdf')
        self.assertRaises(TypeError, zmq.Frame, s)
        u = '§'
        if str is not unicode:
            u = u.decode('utf8')
        for i in range(16):
            s = (2**i)*u
            m = zmq.Frame(s.encode('utf8'))
            self.assertEquals(s, unicode(m.bytes,'utf8'))

    def test_len(self):
        """Test the len of the Frames."""
        for i in range(16):
            s = (2**i)*x
            m = zmq.Frame(s)
            self.assertEquals(len(s), len(m))

    def test_lifecycle1(self):
        """Run through a ref counting cycle with a copy."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*x
            rc = 2
            self.assertEquals(grc(s), rc)
            m = zmq.Frame(s)
            rc += 2
            self.assertEquals(grc(s), rc)
            m2 = copy.copy(m)
            rc += 1
            self.assertEquals(grc(s), rc)
            b = m2.buffer

            rc += view_rc
            self.assertEquals(grc(s), rc)

            self.assertEquals(s, asbytes(str(m)))
            self.assertEquals(s, asbytes(m2))
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
            m = zmq.Frame(s)
            rc += 2
            self.assertEquals(grc(s), rc)
            m2 = copy.copy(m)
            rc += 1
            self.assertEquals(grc(s), rc)
            b = m.buffer
            rc += view_rc
            self.assertEquals(grc(s), rc)
            self.assertEquals(s, asbytes(str(m)))
            self.assertEquals(s, asbytes(m2))
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
        m = zmq.Frame(b'asdf', track=True)
        self.assertFalse(m.tracker.done)
        pm = zmq.MessageTracker(m)
        self.assertFalse(pm.done)
        del m
        self.assertTrue(pm.done)
    
    def test_no_tracker(self):
        m = zmq.Frame(b'asdf', track=False)
        self.assertEquals(m.tracker, None)
        m2 = copy.copy(m)
        self.assertEquals(m2.tracker, None)
        self.assertRaises(ValueError, zmq.MessageTracker, m)
    
    def test_multi_tracker(self):
        m = zmq.Frame(b'asdf', track=True)
        m2 = zmq.Frame(b'whoda', track=True)
        mt = zmq.MessageTracker(m,m2)
        self.assertFalse(m.tracker.done)
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
        m = zmq.Frame(view(ins))
    
    def test_bad_buffer_in(self):
        """test using a bad object"""
        self.assertRaises(TypeError, zmq.Frame, 5)
        self.assertRaises(TypeError, zmq.Frame, object())
        
    def test_buffer_out(self):
        """receiving buffered output"""
        if unicode is str:
            ins = "§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√".encode('utf8')
        else:
            ins = "§§¶•ªº˜µ¬˚…∆˙åß∂©œ∑´†≈ç√"
        m = zmq.Frame(ins)
        outb = m.buffer
        self.assertTrue(isinstance(outb, view))
        self.assert_(outb is m.buffer)
        self.assert_(m.buffer is m.buffer)
    
    def test_multisend(self):
        """ensure that a message remains intact after multiple sends"""
        a,b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        s = b"message"
        m = zmq.Frame(s)
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
            raise SkipTest("numpy required")
        rand = numpy.random.randint
        shapes = [ rand(2,16) for i in range(5) ]
        for i in range(1,len(shapes)+1):
            shape = shapes[:i]
            A = numpy.random.random(shape)
            m = zmq.Frame(A)
            if view.__name__ == 'buffer':
                self.assertEquals(A.data, m.buffer)
                B = numpy.frombuffer(m.buffer,dtype=A.dtype).reshape(A.shape)
            else:
                self.assertEquals(memoryview(A), m.buffer)
                B = numpy.array(m.buffer,dtype=A.dtype).reshape(A.shape)
            self.assertEquals((A==B).all(), True)
    
    def test_memoryview(self):
        """test messages from memoryview"""
        major,minor = sys.version_info[:2]
        if not (major >= 3 or (major == 2 and minor >= 7)):
            raise SkipTest("memoryviews only in python >= 2.7")

        s = b'carrotjuice'
        v = memoryview(s)
        m = zmq.Frame(s)
        buf = m.buffer
        s2 = buf.tobytes()
        self.assertEquals(s2,s)
        self.assertEquals(m.bytes,s)
    
    def test_noncopying_recv(self):
        """check for clobbering message buffers"""
        null = b'\0'*64
        sa,sb = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        for i in range(32):
            # try a few times
            sb.send(null, copy=False)
            m = sa.recv(copy=False)
            mb = m.bytes
            # buf = view(m)
            buf = m.buffer
            del m
            for i in range(5):
                ff=b'\xff'*(40 + i*10)
                sb.send(ff, copy=False)
                m2 = sa.recv(copy=False)
                if view.__name__ == 'buffer':
                    b = bytes(buf)
                else:
                    b = buf.tobytes()
                self.assertEquals(b, null)
                self.assertEquals(mb, null)
                self.assertEquals(m2.bytes, ff)

    def test_buffer_numpy(self):
        """test non-copying numpy array messages"""
        try:
            import numpy
        except ImportError:
            raise SkipTest("requires numpy")
        if sys.version_info < (2,7):
            raise SkipTest("requires new-style buffer interface (py >= 2.7)")
        rand = numpy.random.randint
        shapes = [ rand(2,5) for i in range(5) ]
        a,b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        dtypes = [int, float, '>i4', 'B']
        for i in range(1,len(shapes)+1):
            shape = shapes[:i]
            for dt in dtypes:
                A = numpy.ndarray(shape, dtype=dt)
                while not (A < 1e400).all():
                    # don't let nan sneak in
                    A = numpy.ndarray(shape, dtype=dt)
                a.send(A, copy=False)
                msg = b.recv(copy=False)
                
                B = array_from_buffer(msg, A.dtype, A.shape)
                self.assertEquals(A.shape, B.shape)
                self.assertTrue((A==B).all())
            A = numpy.ndarray(shape, dtype=[('a', int), ('b', float), ('c', 'a32')])
            A['a'] = 1024
            A['b'] = 1e9
            A['c'] = 'hello there'
            a.send(A, copy=False)
            msg = b.recv(copy=False)
            
            B = array_from_buffer(msg, A.dtype, A.shape)
            self.assertEquals(A.shape, B.shape)
            self.assertTrue((A==B).all())
    
    def test_frame_more(self):
        """test Frame.more attribute"""
        frame = zmq.Frame(b"hello")
        self.assertFalse(frame.more)
        sa,sb = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        sa.send_multipart([b'hi', b'there'])
        frame = self.recv(sb, copy=False)
        self.assertTrue(frame.more)
        frame = self.recv(sb, copy=False)
        self.assertFalse(frame.more)
        

