# Copyright (c) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import zmq
from tornado import gen
from zmq.eventloop import future
from zmq.eventloop.ioloop import IOLoop

from zmq.tests import BaseZMQTestCase

class TestFutureSocket(BaseZMQTestCase):
    Context = future.Context
    
    def setUp(self):
        super(TestFutureSocket, self).setUp()
        self.loop = IOLoop.current()
    
    def test_socket_class(self):
        s = self.context.socket(zmq.PUSH)
        assert isinstance(s, future.Socket)
        s.close()
    
    def test_recv_multipart(self):
        a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
        f = b.recv_multipart()
        assert not f.done()
        a.send(b'hi')
        self.loop.run_sync(lambda : f)
        assert f.done()
        self.assertEqual(f.result(), [b'hi'])

    def test_recv(self):
        a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
        f1 = b.recv()
        f2 = b.recv()
        assert not f1.done()
        assert not f2.done()
        self.loop.run_sync(lambda : a.send_multipart([b'hi', b'there']))
        self.loop.run_sync(lambda : f2)
        assert f1.done()
        self.assertEqual(f1.result(), b'hi')
        assert f2.done()
        self.assertEqual(f2.result(), b'there')

    def test_recv_cancel(self):
        a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
        f1 = b.recv()
        f2 = b.recv_multipart()
        assert f1.cancel()
        assert f1.done()
        assert not f2.done()
        self.loop.run_sync(lambda : a.send_multipart([b'hi', b'there']))
        self.loop.run_sync(lambda : f2)
        assert f1.cancelled()
        assert f2.done()
        self.assertEqual(f2.result(), [b'hi', b'there'])


    def test_poll(self):
        a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
        f = b.poll(timeout=0)
        assert f.done()
        self.assertEqual(f.result(), 0)
        
        f = b.poll(timeout=1)
        assert not f.done()
        self.loop.run_sync(lambda : f)
        assert f.done()
        self.assertEqual(f.result(), 0)
        
        f = b.poll(timeout=1000)
        assert not f.done()
        a.send_multipart([b'hi', b'there'])
        self.loop.run_sync(lambda : f)
        assert f.done()
        self.assertEqual(f.result(), zmq.POLLIN)
        recvd = self.loop.run_sync(b.recv_multipart)
        self.assertEqual(recvd, [b'hi', b'there'])
