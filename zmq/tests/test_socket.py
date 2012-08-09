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

import sys
import time
import errno

import zmq
from zmq.tests import BaseZMQTestCase, SkipTest, have_gevent, GreenTest
from zmq.utils.strtypes import bytes, unicode

try:
    from queue import Queue
except:
    from Queue import Queue

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestSocket(BaseZMQTestCase):

    def test_create(self):
        ctx = self.Context()
        s = ctx.socket(zmq.PUB)
        # Superluminal protocol not yet implemented
        self.assertRaisesErrno(zmq.EPROTONOSUPPORT, s.bind, 'ftl://a')
        self.assertRaisesErrno(zmq.EPROTONOSUPPORT, s.connect, 'ftl://a')
        self.assertRaisesErrno(zmq.EINVAL, s.bind, 'tcp://')
        s.close()
        del ctx
    
    def test_unicode_sockopts(self):
        """test setting/getting sockopts with unicode strings"""
        topic = "tést"
        if str is not unicode:
            topic = topic.decode('utf8')
        p,s = self.create_bound_pair(zmq.PUB, zmq.SUB)
        self.assertEquals(s.send_unicode, s.send_unicode)
        self.assertEquals(p.recv_unicode, p.recv_unicode)
        self.assertRaises(TypeError, s.setsockopt, zmq.SUBSCRIBE, topic)
        self.assertRaises(TypeError, s.setsockopt, zmq.IDENTITY, topic)
        s.setsockopt_unicode(zmq.IDENTITY, topic, 'utf16')
        self.assertRaises(TypeError, s.setsockopt, zmq.AFFINITY, topic)
        s.setsockopt_unicode(zmq.SUBSCRIBE, topic)
        self.assertRaises(TypeError, s.getsockopt_unicode, zmq.AFFINITY)
        self.assertRaisesErrno(zmq.EINVAL, s.getsockopt_unicode, zmq.SUBSCRIBE)
        
        st = s.getsockopt(zmq.IDENTITY)
        self.assertEquals(st.decode('utf16'), s.getsockopt_unicode(zmq.IDENTITY, 'utf16'))
        time.sleep(0.1) # wait for connection/subscription
        p.send_unicode(topic,zmq.SNDMORE)
        p.send_unicode(topic*2, encoding='latin-1')
        self.assertEquals(topic, s.recv_unicode())
        self.assertEquals(topic*2, s.recv_unicode(encoding='latin-1'))
    
    def test_int_sockopts(self):
        "test non-uint64 sockopts"
        v = zmq.zmq_version_info()
        if not v >= (2,1):
            raise SkipTest("only on libzmq >= 2.1")
        elif v < (3,0):
            hwm = zmq.HWM
            default_hwm = 0
        else:
            hwm = zmq.SNDHWM
            default_hwm = 1000
        p,s = self.create_bound_pair(zmq.PUB, zmq.SUB)
        p.setsockopt(zmq.LINGER, 0)
        self.assertEquals(p.getsockopt(zmq.LINGER), 0)
        p.setsockopt(zmq.LINGER, -1)
        self.assertEquals(p.getsockopt(zmq.LINGER), -1)
        self.assertEquals(p.getsockopt(hwm), default_hwm)
        p.setsockopt(hwm, 11)
        self.assertEquals(p.getsockopt(hwm), 11)
        # p.setsockopt(zmq.EVENTS, zmq.POLLIN)
        self.assertEquals(p.getsockopt(zmq.EVENTS), zmq.POLLOUT)
        self.assertRaisesErrno(zmq.EINVAL, p.setsockopt,zmq.EVENTS, 2**7-1)
        self.assertEquals(p.getsockopt(zmq.TYPE), p.socket_type)
        self.assertEquals(p.getsockopt(zmq.TYPE), zmq.PUB)
        self.assertEquals(s.getsockopt(zmq.TYPE), s.socket_type)
        self.assertEquals(s.getsockopt(zmq.TYPE), zmq.SUB)
        
        # check for overflow / wrong type:
        errors = []
        backref = {}
        constants = zmq.core.constants
        for name in constants.__all__:
            value = getattr(constants, name)
            if isinstance(value, int):
                backref[value] = name
        for opt in zmq.core.constants.int_sockopts+zmq.core.constants.int64_sockopts:
            sopt = backref[opt]
            if sopt == 'ROUTER_BEHAVIOR' or 'TCP' in sopt:
                # fail_unroutable is write-only
                continue
            try:
                n = p.getsockopt(opt)
            except zmq.ZMQError as e:
                errors.append("getsockopt(zmq.%s) raised '%s'."%(sopt, e))
            else:
                if n > 2**31:
                    errors.append("getsockopt(zmq.%s) returned a ridiculous value."
                                    " It is probably the wrong type."%sopt)
        if errors:
            self.fail('\n'.join([''] + errors))
    
    def test_bad_sockopts(self):
        """Test that appropriate errors are raised on bad socket options"""
        s = self.context.socket(zmq.PUB)
        self.sockets.append(s)
        s.setsockopt(zmq.LINGER, 0)
        # unrecognized int sockopts pass through to libzmq, and should raise EINVAL
        self.assertRaisesErrno(zmq.EINVAL, s.setsockopt, 9999, 5)
        self.assertRaisesErrno(zmq.EINVAL, s.getsockopt, 9999)
        # but only int sockopts are allowed through this way, otherwise raise a TypeError
        self.assertRaises(TypeError, s.setsockopt, 9999, b"5")
        # some sockopts are valid in general, but not on every socket:
        self.assertRaisesErrno(zmq.EINVAL, s.setsockopt, zmq.SUBSCRIBE, b'hi')
    
    def test_sockopt_roundtrip(self):
        "test set/getsockopt roundtrip."
        p = self.context.socket(zmq.PUB)
        self.sockets.append(p)
        self.assertEquals(p.getsockopt(zmq.LINGER), -1)
        p.setsockopt(zmq.LINGER, 11)
        self.assertEquals(p.getsockopt(zmq.LINGER), 11)
    
    def test_poll(self):
        """test Socket.poll()"""
        req, rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        # default flag is POLLIN, nobody has anything to recv:
        self.assertEquals(req.poll(0), 0)
        self.assertEquals(rep.poll(0), 0)
        self.assertEquals(req.poll(0, zmq.POLLOUT), zmq.POLLOUT)
        self.assertEquals(rep.poll(0, zmq.POLLOUT), 0)
        self.assertEquals(req.poll(0, zmq.POLLOUT|zmq.POLLIN), zmq.POLLOUT)
        self.assertEquals(rep.poll(0, zmq.POLLOUT), 0)
        req.send('hi')
        self.assertEquals(req.poll(0), 0)
        self.assertEquals(rep.poll(1), zmq.POLLIN)
        self.assertEquals(req.poll(0, zmq.POLLOUT), 0)
        self.assertEquals(rep.poll(0, zmq.POLLOUT), 0)
        self.assertEquals(req.poll(0, zmq.POLLOUT|zmq.POLLIN), 0)
        self.assertEquals(rep.poll(0, zmq.POLLOUT), zmq.POLLIN)
    
    def test_send_unicode(self):
        "test sending unicode objects"
        a,b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        self.sockets.extend([a,b])
        u = "çπ§"
        if str is not unicode:
            u = u.decode('utf8')
        self.assertRaises(TypeError, a.send, u,copy=False)
        self.assertRaises(TypeError, a.send, u,copy=True)
        a.send_unicode(u)
        s = b.recv()
        self.assertEquals(s,u.encode('utf8'))
        self.assertEquals(s.decode('utf8'),u)
        a.send_unicode(u,encoding='utf16')
        s = b.recv_unicode(encoding='utf16')
        self.assertEquals(s,u)
        
    def test_tracker(self):
        "test the MessageTracker object for tracking when zmq is done with a buffer"
        addr = 'tcp://127.0.0.1'
        a = self.context.socket(zmq.PUB)
        port = a.bind_to_random_port(addr)
        a.close()
        iface = "%s:%i"%(addr,port)
        a = self.context.socket(zmq.PAIR)
        # a.setsockopt(zmq.IDENTITY, b"a")
        b = self.context.socket(zmq.PAIR)
        self.sockets.extend([a,b])
        a.connect(iface)
        time.sleep(0.1)
        p1 = a.send(b'something', copy=False, track=True)
        self.assertTrue(isinstance(p1, zmq.MessageTracker))
        self.assertFalse(p1.done)
        p2 = a.send_multipart([b'something', b'else'], copy=False, track=True)
        self.assert_(isinstance(p2, zmq.MessageTracker))
        self.assertEquals(p2.done, False)
        self.assertEquals(p1.done, False)

        b.bind(iface)
        msg = b.recv_multipart()
        self.assertEquals(p1.done, True)
        self.assertEquals(msg, [b'something'])
        msg = b.recv_multipart()
        self.assertEquals(p2.done, True)
        self.assertEquals(msg, [b'something', b'else'])
        m = zmq.Frame(b"again", track=True)
        self.assertEquals(m.tracker.done, False)
        p1 = a.send(m, copy=False)
        p2 = a.send(m, copy=False)
        self.assertEquals(m.tracker.done, False)
        self.assertEquals(p1.done, False)
        self.assertEquals(p2.done, False)
        msg = b.recv_multipart()
        self.assertEquals(m.tracker.done, False)
        self.assertEquals(msg, [b'again'])
        msg = b.recv_multipart()
        self.assertEquals(m.tracker.done, False)
        self.assertEquals(msg, [b'again'])
        self.assertEquals(p1.done, False)
        self.assertEquals(p2.done, False)
        pm = m.tracker
        del m
        time.sleep(0.1)
        self.assertEquals(p1.done, True)
        self.assertEquals(p2.done, True)
        m = zmq.Frame(b'something', track=False)
        self.assertRaises(ValueError, a.send, m, copy=False, track=True)
        

    def test_close(self):
        ctx = self.Context()
        s = ctx.socket(zmq.PUB)
        s.close()
        self.assertRaises(zmq.ZMQError, s.bind, b'')
        self.assertRaises(zmq.ZMQError, s.connect, b'')
        self.assertRaises(zmq.ZMQError, s.setsockopt, zmq.SUBSCRIBE, b'')
        self.assertRaises(zmq.ZMQError, s.send, b'asdf')
        self.assertRaises(zmq.ZMQError, s.recv)
        del ctx
    
    def test_attr(self):
        """set setting/getting sockopts as attributes"""
        s = self.context.socket(zmq.DEALER)
        self.sockets.append(s)
        linger = 10
        s.linger = linger
        self.assertEquals(linger, s.linger)
        self.assertEquals(linger, s.getsockopt(zmq.LINGER))
        self.assertEquals(s.fd, s.getsockopt(zmq.FD))
    
    def test_bad_attr(self):
        s = self.context.socket(zmq.DEALER)
        self.sockets.append(s)
        try:
            s.apple='foo'
        except AttributeError:
            pass
        else:
            self.fail("bad setattr should have raised AttributeError")
        try:
            s.apple
        except AttributeError:
            pass
        else:
            self.fail("bad getattr should have raised AttributeError")

    def test_subclass(self):
        """subclasses can assign attributes"""
        class S(zmq.Socket):
            def __init__(self, *a, **kw):
                self.a=-1
        s = S(self.context, zmq.REP)
        self.sockets.append(s)
        self.assertEquals(s.a, -1)
        s.a=1
        self.assertEquals(s.a, 1)
        a=s.a
        self.assertEquals(a, 1)
    
    def test_recv_multipart(self):
        a,b = self.create_bound_pair()
        msg = b'hi'
        for i in range(3):
            a.send(msg)
        time.sleep(0.1)
        for i in range(3):
            self.assertEquals(b.recv_multipart(), [msg])
    
    def test_close_after_destroy(self):
        """s.close() after ctx.destroy() should be fine"""
        ctx = self.Context()
        s = ctx.socket(zmq.REP)
        ctx.destroy()
        # reaper is not instantaneous
        time.sleep(1e-2)
        s.close()
        self.assertTrue(s.closed)
    
    def test_poll(self):
        a,b = self.create_bound_pair()
        tic = time.time()
        evt = a.poll(50)
        self.assertEquals(evt, 0)
        evt = a.poll(50, zmq.POLLOUT)
        self.assertEquals(evt, zmq.POLLOUT)
        msg = b'hi'
        a.send(msg)
        evt = b.poll(50)
        self.assertEquals(evt, zmq.POLLIN)
        msg2 = self.recv(b)
        evt = b.poll(50)
        self.assertEquals(evt, 0)
        self.assertEquals(msg2, msg)
    
    def test_ipc_path_max_length(self):
        """IPC_PATH_MAX_LEN is a sensible value"""
        if zmq.IPC_PATH_MAX_LEN == 0:
            raise SkipTest("IPC_PATH_MAX_LEN undefined")
        
        msg = "Surprising value for IPC_PATH_MAX_LEN: %s" % zmq.IPC_PATH_MAX_LEN
        self.assertTrue(zmq.IPC_PATH_MAX_LEN > 30, msg)
        self.assertTrue(zmq.IPC_PATH_MAX_LEN < 1025, msg)

    def test_ipc_path_max_length_msg(self):
        if zmq.IPC_PATH_MAX_LEN == 0:
            raise SkipTest("IPC_PATH_MAX_LEN undefined")
        
        s = self.context.socket(zmq.PUB)
        self.sockets.append(s)
        try:
            s.bind('ipc://{0}'.format('a' * (zmq.IPC_PATH_MAX_LEN + 1)))
        except zmq.ZMQError as e:
            self.assertTrue(str(zmq.IPC_PATH_MAX_LEN) in e.strerror)


if have_gevent:
    import gevent
    
    class TestSocketGreen(GreenTest, TestSocket):
        test_bad_attr = GreenTest.skip_green
        test_close_after_destroy = GreenTest.skip_green
        
        def test_timeout(self):
            a,b = self.create_bound_pair()
            g = gevent.spawn_later(0.5, lambda: a.send(b'hi'))
            timeout = gevent.Timeout(0.1)
            timeout.start()
            self.assertRaises(gevent.Timeout, b.recv)
            g.kill()


