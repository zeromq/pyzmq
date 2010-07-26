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
    
    def test_unicode_ascii(self):
        """test using unicode simple strings"""
        p,s = self.create_bound_pair(zmq.PUB, zmq.SUB)
        s.setsockopt(zmq.SUBSCRIBE, u"test")
        time.sleep(0.1)
        msg = [ "test", u"msg content" ]
        p.send_multipart(msg)
        rcvd = s.recv_multipart()
        for a,b in zip(msg, rcvd):
            self.assertEquals(a,b)
    
    def test_unicode_sockopts(self):
        p,s = self.create_bound_pair(zmq.PUB, zmq.SUB)
        s.setsockopt(zmq.SUBSCRIBE, u'ascii')
        utopic =  u"çπ§"
        self.assertRaises(UnicodeEncodeError, s.setsockopt, zmq.SUBSCRIBE,utopic)
        s.setsockopt(zmq.SUBSCRIBE, str(buffer(utopic)))
        msg = ['ascii', 'yes']
        time.sleep(0.1)
        p.send_multipart(msg)
        rcvd = s.recv_multipart()
        for a,b in zip(msg, rcvd):
            self.assertEquals(a,b)
        msg = [utopic, 'yes']
        # time.sleep(0.1)
        p.send_multipart(msg)
        rcvd = s.recv_multipart()
        rcvd[0] = rcvd[0].decode('utf16')
        for a,b in zip(msg, rcvd):
            self.assertEquals(a,b)
        
        
    
    def test_unicode_nonascii(self):
        """test sending non-ascii unicode characters"""
        p,s = self.create_bound_pair(zmq.PUB, zmq.SUB)
        s.setsockopt(zmq.SUBSCRIBE, "test")
        time.sleep(0.1)
        msg = [ u"test", u"msg∆˚¬content∂" ]
        p.send_multipart(msg)
        rcvd = s.recv_multipart()
        rcvd[1] = rcvd[1].decode('utf16')
        for a,b in zip(msg,rcvd):
            self.assertEquals(a,b)
    
    # def test_nonunicode(self):

    def test_close(self):
        ctx = zmq.Context()
        s = ctx.socket(zmq.PUB)
        s.close()
        self.assertRaises(zmq.ZMQError, s.bind, '')
        self.assertRaises(zmq.ZMQError, s.connect, '')
        self.assertRaises(zmq.ZMQError, s.setsockopt, zmq.SUBSCRIBE, '')
        self.assertRaises(zmq.ZMQError, s.send, 'asdf')
        self.assertRaises(zmq.ZMQError, s.recv)

