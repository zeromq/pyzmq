# coding: utf-8
# Copyright (c) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from datetime import timedelta
import os

import pytest
gen = pytest.importorskip('tornado.gen')

import zmq
from zmq.eventloop import future
from zmq.eventloop.ioloop import IOLoop
from zmq.utils.strtypes import u

from zmq.tests import BaseZMQTestCase

class TestFutureSocket(BaseZMQTestCase):
    Context = future.Context
    
    def setUp(self):
        self.loop = IOLoop()
        self.loop.make_current()
        super(TestFutureSocket, self).setUp()
    
    def tearDown(self):
        super(TestFutureSocket, self).tearDown()
        self.loop.close(all_fds=True)
    
    def test_socket_class(self):
        s = self.context.socket(zmq.PUSH)
        assert isinstance(s, future.Socket)
        s.close()

    def test_recv_multipart(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_multipart()
            assert not f.done()
            yield a.send(b'hi')
            recvd = yield f
            self.assertEqual(recvd, [b'hi'])
        self.loop.run_sync(test)

    def test_recv(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f1 = b.recv()
            f2 = b.recv()
            assert not f1.done()
            assert not f2.done()
            yield  a.send_multipart([b'hi', b'there'])
            recvd = yield f2
            assert f1.done()
            self.assertEqual(f1.result(), b'hi')
            self.assertEqual(recvd, b'there')
        self.loop.run_sync(test)

    def test_recv_cancel(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f1 = b.recv()
            f2 = b.recv_multipart()
            assert f1.cancel()
            assert f1.done()
            assert not f2.done()
            yield  a.send_multipart([b'hi', b'there'])
            recvd = yield f2
            assert f1.cancelled()
            assert f2.done()
            self.assertEqual(recvd, [b'hi', b'there'])
        self.loop.run_sync(test)

    @pytest.mark.skipif(not hasattr(zmq, 'RCVTIMEO'), reason="requires RCVTIMEO")
    def test_recv_timeout(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            b.rcvtimeo = 100
            f1 = b.recv()
            b.rcvtimeo = 1000
            f2 = b.recv_multipart()
            with pytest.raises(zmq.Again):
                yield f1
            yield  a.send_multipart([b'hi', b'there'])
            recvd = yield f2
            assert f2.done()
            self.assertEqual(recvd, [b'hi', b'there'])
        self.loop.run_sync(test)

    @pytest.mark.skipif(not hasattr(zmq, 'SNDTIMEO'), reason="requires SNDTIMEO")
    def test_send_timeout(self):
        @gen.coroutine
        def test():
            s = self.socket(zmq.PUSH)
            s.sndtimeo = 100
            with pytest.raises(zmq.Again):
                yield s.send(b'not going anywhere')
        self.loop.run_sync(test)
    
    @pytest.mark.now
    def test_send_noblock(self):
        @gen.coroutine
        def test():
            s = self.socket(zmq.PUSH)
            with pytest.raises(zmq.Again):
                yield s.send(b'not going anywhere', flags=zmq.NOBLOCK)
        self.loop.run_sync(test)

    @pytest.mark.now
    def test_send_multipart_noblock(self):
        @gen.coroutine
        def test():
            s = self.socket(zmq.PUSH)
            with pytest.raises(zmq.Again):
                yield s.send_multipart([b'not going anywhere'], flags=zmq.NOBLOCK)
        self.loop.run_sync(test)

    def test_recv_string(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_string()
            assert not f.done()
            msg = u('πøøπ')
            yield a.send_string(msg)
            recvd = yield f
            assert f.done()
            self.assertEqual(f.result(), msg)
            self.assertEqual(recvd, msg)
        self.loop.run_sync(test)

    def test_recv_json(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_json()
            assert not f.done()
            obj = dict(a=5)
            yield a.send_json(obj)
            recvd = yield f
            assert f.done()
            self.assertEqual(f.result(), obj)
            self.assertEqual(recvd, obj)
        self.loop.run_sync(test)

    def test_recv_json_cancelled(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_json()
            assert not f.done()
            f.cancel()
            # cycle eventloop to allow cancel events to fire
            yield gen.sleep(0)
            obj = dict(a=5)
            yield a.send_json(obj)
            with pytest.raises(future.CancelledError):
                recvd = yield f
            assert f.done()
            # give it a chance to incorrectly consume the event
            events = yield b.poll(timeout=5)
            assert events
            yield gen.sleep(0)
            # make sure cancelled recv didn't eat up event
            recvd = yield gen.with_timeout(timedelta(seconds=5), b.recv_json())
            assert recvd == obj
        self.loop.run_sync(test)

    def test_recv_pyobj(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_pyobj()
            assert not f.done()
            obj = dict(a=5)
            yield a.send_pyobj(obj)
            recvd = yield f
            assert f.done()
            self.assertEqual(f.result(), obj)
            self.assertEqual(recvd, obj)
        self.loop.run_sync(test)

    def test_poll(self):
        @gen.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.poll(timeout=0)
            self.assertEqual(f.result(), 0)

            f = b.poll(timeout=1)
            assert not f.done()
            evt = yield f
            self.assertEqual(evt, 0)

            f = b.poll(timeout=1000)
            assert not f.done()
            yield a.send_multipart([b'hi', b'there'])
            evt = yield f
            self.assertEqual(evt, zmq.POLLIN)
            recvd = yield b.recv_multipart()
            self.assertEqual(recvd, [b'hi', b'there'])
        self.loop.run_sync(test)

    def test_poll_raw(self):
        @gen.coroutine
        def test():
            p = future.Poller()
            # make a pipe
            r, w = os.pipe()
            r = os.fdopen(r, 'rb')
            w = os.fdopen(w, 'wb')

            # POLLOUT
            p.register(r, zmq.POLLIN)
            p.register(w, zmq.POLLOUT)
            evts = yield p.poll(timeout=1)
            evts = dict(evts)
            assert r.fileno() not in evts
            assert w.fileno() in evts
            assert evts[w.fileno()] == zmq.POLLOUT

            # POLLIN
            p.unregister(w)
            w.write(b'x')
            w.flush()
            evts = yield p.poll(timeout=1000)
            evts = dict(evts)
            assert r.fileno() in evts
            assert evts[r.fileno()] == zmq.POLLIN
            assert r.read(1) == b'x'
            r.close()
            w.close()
        self.loop.run_sync(test)
