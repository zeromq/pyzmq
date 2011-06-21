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
from zmq.utils.strtypes import asbytes
from zmq.tests import BaseZMQTestCase


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


class TestContext(BaseZMQTestCase):

    def test_init(self):
        c1 = zmq.Context()
        self.assert_(isinstance(c1, zmq.Context))
        del c1
        c2 = zmq.Context()
        self.assert_(isinstance(c2, zmq.Context))
        del c2
        c3 = zmq.Context()
        self.assert_(isinstance(c3, zmq.Context))
        del c3

    def test_term(self):
        c = zmq.Context()
        c.term()
        self.assert_(c.closed)

    def test_fail_init(self):
        self.assertRaisesErrno(zmq.EINVAL, zmq.Context, 0)
    
    def test_term_hang(self):
        rep,req = self.create_bound_pair(zmq.ROUTER, zmq.DEALER)
        req.setsockopt(zmq.LINGER, 0)
        req.send(asbytes('hello'), copy=False)
        req.close()
        rep.close()
        self.context.term()
    
    def test_instance(self):
        ctx = zmq.Context.instance()
        c2 = zmq.Context.instance(io_threads=2)
        self.assertTrue(c2 is ctx)
        c2.term()
        c3 = zmq.Context.instance()
        c4 = zmq.Context.instance()
        self.assertFalse(c3 is c2)
        self.assertFalse(c3.closed)
        self.assertTrue(c3 is c4)
        

