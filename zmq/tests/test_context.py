#
#    Copyright (c) 2010-2011 Brian E. Granger & Min Ragan-Kelley
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

import sys
import time
from threading import Thread

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
    
    def test_many_sockets(self):
        """opening and closing many sockets shouldn't cause problems"""
        ctx = zmq.Context()
        for i in range(16):
            sockets = [ ctx.socket(zmq.REP) for i in range(65) ]
            [ s.close() for s in sockets ]
            # give the reaper a chance
            time.sleep(1e-2)
        ctx.term()
    
    def test_shutdown(self):
        """Context.shutdown should close sockets"""
        ctx = zmq.Context()
        sockets = [ ctx.socket(zmq.REP) for i in range(65) ]
        
        # close half of the sockets
        [ s.close() for s in sockets[::2] ]
        
        ctx.shutdown()
        # reaper is not instantaneous
        time.sleep(1e-2)
        for s in sockets:
            self.assertTrue(s.closed)
        
    def test_shutdown_linger(self):
        """Context.shutdown should set linger on closing sockets"""
        req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        req.send(asbytes('hi'))
        self.context.shutdown(linger=0)
        # reaper is not instantaneous
        time.sleep(1e-2)
        for s in (req,rep):
            self.assertTrue(s.closed)
        
    def test_term_noclose(self):
        """Context.term won't close sockets"""
        ctx = zmq.Context()
        s = ctx.socket(zmq.REQ)
        self.assertFalse(s.closed)
        t = Thread(target=ctx.term)
        t.start()
        t.join(timeout=0.1)
        if sys.version[:3] == '2.5':
            t.is_alive = t.isAlive
        self.assertTrue(t.is_alive(), "Context should be waiting")
        s.close()
        t.join(timeout=0.1)
        self.assertFalse(t.is_alive(), "Context should have closed")

