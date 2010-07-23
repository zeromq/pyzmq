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
    
    def test_unicode(self):
        ctx = zmq.Context()
        p = ctx.socket(zmq.PUB)
        p.bind(u"inproc://foo")
        s = ctx.socket(zmq.SUB)
        s.connect(u"inproc://foo")
        s.setsockopt(zmq.SUBSCRIBE, u"test")
        msg = [ "test", u"msg content" ]
        p.send_multipart(msg)
        rcvd = s.recv_multipart()
        for a,b in zip(msg, rcvd):
            self.assertEquals(a,b)

    def test_close(self):
        ctx = zmq.Context()
        s = ctx.socket(zmq.PUB)
        s.close()
        self.assertRaises(zmq.ZMQError, s.bind, '')
        self.assertRaises(zmq.ZMQError, s.connect, '')
        self.assertRaises(zmq.ZMQError, s.setsockopt, zmq.SUBSCRIBE, '')
        self.assertRaises(zmq.ZMQError, s.send, 'asdf')
        self.assertRaises(zmq.ZMQError, s.recv)

