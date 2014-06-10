# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import gc
import sys
import time
from threading import Thread, Event

import zmq
from zmq.tests import (
    BaseZMQTestCase, have_gevent, GreenTest, skip_green, PYPY, SkipTest,
)


class TestContext(BaseZMQTestCase):

    def test_init(self):
        c1 = self.Context()
        self.assert_(isinstance(c1, self.Context))
        del c1
        c2 = self.Context()
        self.assert_(isinstance(c2, self.Context))
        del c2
        c3 = self.Context()
        self.assert_(isinstance(c3, self.Context))
        del c3

    def test_dir(self):
        ctx = self.Context()
        self.assertTrue('socket' in dir(ctx))
        if zmq.zmq_version_info() > (3,):
            self.assertTrue('IO_THREADS' in dir(ctx))
        ctx.term()

    def test_term(self):
        c = self.Context()
        c.term()
        self.assert_(c.closed)
    
    def test_context_manager(self):
        with self.Context() as c:
            pass
        self.assert_(c.closed)
    
    def test_fail_init(self):
        self.assertRaisesErrno(zmq.EINVAL, self.Context, -1)
    
    def test_term_hang(self):
        rep,req = self.create_bound_pair(zmq.ROUTER, zmq.DEALER)
        req.setsockopt(zmq.LINGER, 0)
        req.send(b'hello', copy=False)
        req.close()
        rep.close()
        self.context.term()
    
    def test_instance(self):
        ctx = self.Context.instance()
        c2 = self.Context.instance(io_threads=2)
        self.assertTrue(c2 is ctx)
        c2.term()
        c3 = self.Context.instance()
        c4 = self.Context.instance()
        self.assertFalse(c3 is c2)
        self.assertFalse(c3.closed)
        self.assertTrue(c3 is c4)
    
    def test_many_sockets(self):
        """opening and closing many sockets shouldn't cause problems"""
        ctx = self.Context()
        for i in range(16):
            sockets = [ ctx.socket(zmq.REP) for i in range(65) ]
            [ s.close() for s in sockets ]
            # give the reaper a chance
            time.sleep(1e-2)
        ctx.term()
    
    def test_sockopts(self):
        """setting socket options with ctx attributes"""
        ctx = self.Context()
        ctx.linger = 5
        self.assertEqual(ctx.linger, 5)
        s = ctx.socket(zmq.REQ)
        self.assertEqual(s.linger, 5)
        self.assertEqual(s.getsockopt(zmq.LINGER), 5)
        s.close()
        # check that subscribe doesn't get set on sockets that don't subscribe:
        ctx.subscribe = b''
        s = ctx.socket(zmq.REQ)
        s.close()
        
        ctx.term()

    
    def test_destroy(self):
        """Context.destroy should close sockets"""
        ctx = self.Context()
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
        req.send(b'hi')
        time.sleep(1e-2)
        self.context.destroy(linger=0)
        # reaper is not instantaneous
        time.sleep(1e-2)
        for s in (req,rep):
            self.assertTrue(s.closed)
        
    def test_term_noclose(self):
        """Context.term won't close sockets"""
        ctx = self.Context()
        s = ctx.socket(zmq.REQ)
        self.assertFalse(s.closed)
        t = Thread(target=ctx.term)
        t.start()
        t.join(timeout=0.1)
        self.assertTrue(t.is_alive(), "Context should be waiting")
        s.close()
        t.join(timeout=0.1)
        self.assertFalse(t.is_alive(), "Context should have closed")
    
    def test_gc(self):
        """test close&term by garbage collection alone"""
        if PYPY:
            raise SkipTest("GC doesn't work ")
            
        # test credit @dln (GH #137):
        def gcf():
            def inner():
                ctx = self.Context()
                s = ctx.socket(zmq.PUSH)
            inner()
            gc.collect()
        t = Thread(target=gcf)
        t.start()
        t.join(timeout=1)
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
            ctx = self.Context()
            sock = ctx.socket(zmq.PULL)
            c = CyclicReference()
            c.crash(sock)
            ctx.destroy()
        
        crash_zmq()
    
    def test_term_thread(self):
        """ctx.term should not crash active threads (#139)"""
        ctx = self.Context()
        evt = Event()
        evt.clear()

        def block():
            s = ctx.socket(zmq.REP)
            s.bind_to_random_port('tcp://127.0.0.1')
            evt.set()
            try:
                s.recv()
            except zmq.ZMQError as e:
                self.assertEqual(e.errno, zmq.ETERM)
                return
            finally:
                s.close()
            self.fail("recv should have been interrupted with ETERM")
        t = Thread(target=block)
        t.start()
        
        evt.wait(1)
        self.assertTrue(evt.is_set(), "sync event never fired")
        time.sleep(0.01)
        ctx.term()
        t.join(timeout=1)
        self.assertFalse(t.is_alive(), "term should have interrupted s.recv()")
    
    def test_destroy_no_sockets(self):
        ctx = self.Context()
        s = ctx.socket(zmq.PUB)
        s.bind_to_random_port('tcp://127.0.0.1')
        s.close()
        ctx.destroy()
        assert s.closed
        assert ctx.closed
    
    def test_ctx_opts(self):
        if zmq.zmq_version_info() < (3,):
            raise SkipTest("context options require libzmq 3")
        ctx = self.Context()
        ctx.set(zmq.MAX_SOCKETS, 2)
        self.assertEqual(ctx.get(zmq.MAX_SOCKETS), 2)
        ctx.max_sockets = 100
        self.assertEqual(ctx.max_sockets, 100)
        self.assertEqual(ctx.get(zmq.MAX_SOCKETS), 100)
    
    def test_shadow(self):
        ctx = self.Context()
        ctx2 = self.Context.shadow(ctx.underlying)
        self.assertEqual(ctx.underlying, ctx2.underlying)
        s = ctx.socket(zmq.PUB)
        s.close()
        del ctx2
        self.assertFalse(ctx.closed)
        s = ctx.socket(zmq.PUB)
        ctx2 = self.Context.shadow(ctx.underlying)
        s2 = ctx2.socket(zmq.PUB)
        s.close()
        s2.close()
        ctx.term()
        self.assertRaisesErrno(zmq.EFAULT, ctx2.socket, zmq.PUB)
        del ctx2
    
    def test_shadow_pyczmq(self):
        try:
            from pyczmq import zctx, zsocket, zstr
        except Exception:
            raise SkipTest("Requires pyczmq")
        
        ctx = zctx.new()
        a = zsocket.new(ctx, zmq.PUSH)
        zsocket.bind(a, "inproc://a")
        ctx2 = self.Context.shadow_pyczmq(ctx)
        b = ctx2.socket(zmq.PULL)
        b.connect("inproc://a")
        zstr.send(a, b'hi')
        rcvd = self.recv(b)
        self.assertEqual(rcvd, b'hi')
        b.close()


if False: # disable green context tests
    class TestContextGreen(GreenTest, TestContext):
        """gevent subclass of context tests"""
        # skip tests that use real threads:
        test_gc = GreenTest.skip_green
        test_term_thread = GreenTest.skip_green
        test_destroy_linger = GreenTest.skip_green
