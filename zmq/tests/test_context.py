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

import sys
import time
from threading import Thread

import zmq
from zmq.utils.strtypes import asbytes, b
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
    
    def test_sockopts(self):
        """setting socket options with ctx attributes"""
        ctx = zmq.Context()
        ctx.linger = 5
        self.assertEquals(ctx.linger, 5)
        s = ctx.socket(zmq.REQ)
        self.assertEquals(s.linger, 5)
        self.assertEquals(s.getsockopt(zmq.LINGER), 5)
        s.close()
        # check that subscribe doesn't get set on sockets that don't subscribe:
        ctx.subscribe = b('')
        s = ctx.socket(zmq.REQ)
        s.close()
        
        ctx.term()

    
    def test_destroy(self):
        """Context.destroy should close sockets"""
        ctx = zmq.Context()
        sockets = [ ctx.socket(zmq.REP) for i in range(65) ]
        
        # close half of the sockets
        [ s.close() for s in sockets[::2] ]
        
        ctx.destroy()
        # reaper is not instantaneous
        time.sleep(1e-2)
        for s in sockets:
            self.assertTrue(s.closed)
        
    def test_destroy_linger(self):
        """Context.destroy should set linger on closing sockets"""
        req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        req.send(asbytes('hi'))
        time.sleep(1e-2)
        self.context.destroy(linger=0)
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
    
    def test_gc(self):
        """test close&term by garbage collection alone"""
        # test credit @dln (GH #137):
        def gc():
            ctx = zmq.Context()
            s = ctx.socket(zmq.PUSH)
        t = Thread(target=gc)
        t.start()
        t.join(timeout=1)
        if sys.version[:3] == '2.5':
            t.is_alive = t.isAlive
        self.assertFalse(t.is_alive(), "Garbage collection should have cleaned up context")
    
    def test_cyclic_destroy(self):
        """ctx.destroy should succeed when cyclic ref prevents gc"""
        # test credit @dln (GH #137):
        class CyclicReference(object):
            def __init__(self, parent=None):
                self.parent = parent
            
            def crash(self, sock):
                self.sock = sock
                self.child = CyclicReference(self)
        
        def crash_zmq():
            ctx = zmq.Context()
            sock = ctx.socket(zmq.PULL)
            c = CyclicReference()
            c.crash(sock)
            ctx.destroy()
        
        crash_zmq()
    
    def test_term_thread(self):
        """ctx.term should not crash active threads (#139)"""
        ctx = zmq.Context()
        def block():
            s = ctx.socket(zmq.REP)
            s.bind_to_random_port('tcp://127.0.0.1')
            try:
                s.recv()
            except zmq.ZMQError:
                e = sys.exc_info()[1]
                if e.errno == zmq.ETERM:
                    # context terminated, this is supposed to happen
                    pass
                else:
                    raise
            s.close()
        t = Thread(target=block)
        t.start()
        if sys.version[:3] == '2.5':
            t.is_alive = t.isAlive
        ctx.term()
        t.join(timeout=1)
        self.assertFalse(t.is_alive(), "term should have interrupted s.recv()")

