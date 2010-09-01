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
import time
import zmq
from zmq.tests import BaseZMQTestCase
try:
    from queue import Queue
except:
    from Queue import Queue

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


class TestSocket(BaseZMQTestCase):

    def test_create(self):
        ctx = zmq.Context()
        s = ctx.socket(zmq.PUB)
        # Superluminal protocol not yet implemented
        self.assertRaisesErrno(zmq.EPROTONOSUPPORT, s.bind, 'ftl://')
        self.assertRaisesErrno(zmq.EPROTONOSUPPORT, s.connect, 'ftl://')
    
    def test_unicode_sockopts(self):
        """test setting/getting sockopts with unicode strings"""
        topic = u"tést"
        p,s = self.create_bound_pair(zmq.PUB, zmq.SUB)
        self.assertEquals(s.send_string, s.send_unicode)
        self.assertEquals(p.recv_string, p.recv_unicode)
        self.assertRaises(TypeError, s.setsockopt, zmq.SUBSCRIBE, topic)
        self.assertRaises(TypeError, s.setsockopt, zmq.IDENTITY, topic)
        self.assertRaises(TypeError, s.setsockopt, zmq.AFFINITY, topic)
        s.setsockopt_unicode(zmq.SUBSCRIBE, topic)
        s.setsockopt_unicode(zmq.IDENTITY, topic, 'utf16')
        self.assertRaises(TypeError, s.getsockopt_unicode, zmq.AFFINITY)
        self.assertRaises(TypeError, s.getsockopt_unicode, zmq.SUBSCRIBE)
        st = s.getsockopt(zmq.IDENTITY)
        self.assertEquals(st.decode('utf16'), s.getsockopt_unicode(zmq.IDENTITY, 'utf16'))
        time.sleep(0.1) # wait for connection/subscription
        p.send_unicode(topic,zmq.SNDMORE)
        p.send_unicode(topic*2, encoding='utf32')
        self.assertEquals(topic, s.recv_unicode())
        self.assertEquals(topic*2, s.recv_unicode(encoding='utf32'))
    
    def test_send_unicode(self):
        "test sending unicode objects"
        a,b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        self.assertEquals(a.setsockopt_string, a.setsockopt_unicode)
        self.assertEquals(b.getsockopt_string, b.getsockopt_unicode)
        u =  u"çπ§"
        self.assertRaises(TypeError, a.send, u,copy=False)
        self.assertRaises(TypeError, a.send, u,copy=True)
        a.send_unicode(u)
        s = b.recv()
        self.assertEquals(s,u.encode('utf8'))
        self.assertEquals(s.decode('utf8'),u)
        a.send_unicode(u,encoding='utf32')
        s = b.recv_unicode(encoding='utf32')
        self.assertEquals(s,u)
        
    def test_pending_message(self):
        "test the PendingMessage object for tracking when zmq is done with a buffer"
        a = self.context.socket(zmq.XREQ)
        a.setsockopt(zmq.IDENTITY, "a")
        b = self.context.socket(zmq.XREP)
        addr = 'tcp://127.0.0.1:12345'
        a.connect(addr)
        p1 = a.send('something', copy=False)
        self.assert_(isinstance(p1, zmq.PendingMessage))
        self.assertTrue(p1.pending)
        p2 = a.send_multipart(['something', 'else'], copy=False)
        self.assert_(isinstance(p2, zmq.PendingMessage))
        self.assertEquals(p2.pending, True)
        self.assertEquals(p1.pending, True)
        b.bind(addr)
        msg = b.recv_multipart()
        self.assertEquals(p1.pending, False)
        self.assertEquals(msg, ['a', 'something'])
        msg = b.recv_multipart()
        self.assertEquals(p2.pending, False)
        self.assertEquals(msg, ['a', 'something', 'else'])
        m = zmq.Message("again")
        self.assertEquals(m.pending, True)
        # print m.bytes
        p1 = a.send(m, copy=False)
        p2 = a.send(m, copy=False)
        self.assertEquals(m.pending, True)
        self.assertEquals(p1.pending, True)
        self.assertEquals(p2.pending, True)
        msg = b.recv_multipart()
        self.assertEquals(m.pending, True)
        self.assertEquals(msg, ['a', 'again'])
        msg = b.recv_multipart()
        self.assertEquals(m.pending, True)
        self.assertEquals(msg, ['a', 'again'])
        self.assertEquals(p1.pending, True)
        self.assertEquals(p2.pending, True)
        pm = m.pending_message
        del m
        time.sleep(0.1)
        # q.get()
        self.assertEquals(p1.pending, False)
        self.assertEquals(p2.pending, False)
        
    
    def test_close(self):
        ctx = zmq.Context()
        s = ctx.socket(zmq.PUB)
        s.close()
        self.assertRaises(zmq.ZMQError, s.bind, '')
        self.assertRaises(zmq.ZMQError, s.connect, '')
        self.assertRaises(zmq.ZMQError, s.setsockopt, zmq.SUBSCRIBE, '')
        self.assertRaises(zmq.ZMQError, s.send, 'asdf')
        self.assertRaises(zmq.ZMQError, s.recv)

