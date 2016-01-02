"""Test asyncio support"""
# Copyright (c) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import zmq
try:
    import asyncio
    import zmq.asyncio as zaio
except ImportError:
    asyncio = None

from zmq.tests import BaseZMQTestCase, SkipTest

class TestAsyncIOSocket(BaseZMQTestCase):
    if asyncio is not None:
        Context = zaio.Context
    
    def setUp(self):
        if asyncio is None:
            raise SkipTest()
        self.loop = zaio.ZMQEventLoop()
        asyncio.set_event_loop(self.loop)
        super(TestAsyncIOSocket, self).setUp()
    
    def tearDown(self):
        self.loop.close()
        super().tearDown()
    
    def test_socket_class(self):
        s = self.context.socket(zmq.PUSH)
        assert isinstance(s, zaio.Socket)
        s.close()
    
    def test_recv_multipart(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_multipart()
            assert not f.done()
            yield from a.send(b'hi')
            recvd = yield from f
            self.assertEqual(recvd, [b'hi'])
        self.loop.run_until_complete(test())

    def test_recv(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f1 = b.recv()
            f2 = b.recv()
            assert not f1.done()
            assert not f2.done()
            yield from  a.send_multipart([b'hi', b'there'])
            recvd = yield from f2
            assert f1.done()
            self.assertEqual(f1.result(), b'hi')
            self.assertEqual(recvd, b'there')
        self.loop.run_until_complete(test())

    def test_recv_cancel(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f1 = b.recv()
            f2 = b.recv_multipart()
            assert f1.cancel()
            assert f1.done()
            assert not f2.done()
            yield from a.send_multipart([b'hi', b'there'])
            recvd = yield from f2
            assert f1.cancelled()
            assert f2.done()
            self.assertEqual(recvd, [b'hi', b'there'])
        self.loop.run_until_complete(test())

    def test_poll(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.poll(timeout=0)
            yield from asyncio.sleep(0)
            self.assertEqual(f.result(), 0)
        
            f = b.poll(timeout=1)
            assert not f.done()
            evt = yield from f
            
            self.assertEqual(evt, 0)
        
            f = b.poll(timeout=1000)
            assert not f.done()
            yield from a.send_multipart([b'hi', b'there'])
            evt = yield from f
            self.assertEqual(evt, zmq.POLLIN)
            recvd = yield from b.recv_multipart()
            self.assertEqual(recvd, [b'hi', b'there'])
        self.loop.run_until_complete(test())
    
    def test_aiohttp(self):
        try:
            import aiohttp
        except ImportError:
            raise SkipTest("Requires aiohttp")
        from aiohttp import web
        
        zmq.asyncio.install()
        
        @asyncio.coroutine
        def echo(request):
            print(request.path)
            return web.Response(body=str(request).encode('utf8'))
        
        @asyncio.coroutine
        def server(loop):
            app = web.Application(loop=loop)
            app.router.add_route('GET', '/', echo)

            srv = yield from loop.create_server(app.make_handler(),
                                                '127.0.0.1', 8080)
            print("Server started at http://127.0.0.1:8080")
            return srv

        @asyncio.coroutine
        def client():
            push, pull = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            
            res = yield from aiohttp.request('GET', 'http://127.0.0.1:8080/')
            text = yield from res.text()
            yield from push.send(text.encode('utf8'))
            rcvd = yield from pull.recv()
            self.assertEqual(rcvd.decode('utf8'), text)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(server(loop))
        print("servered")
        loop.run_until_complete(client())
