# Copyright (c) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import zmq
from tornado import gen
from zmq.eventloop import future
from zmq.eventloop.ioloop import IOLoop

from zmq.tests import BaseZMQTestCase
from tornado import gen

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
