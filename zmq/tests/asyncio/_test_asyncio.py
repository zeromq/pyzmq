"""Test asyncio support"""
# Copyright (c) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import os
import sys

import pytest
from pytest import mark

import zmq
from zmq.utils.strtypes import u

try:
    import asyncio
    import zmq.asyncio as zaio
    from zmq.auth.asyncio import AsyncioAuthenticator
except ImportError:
    if sys.version_info >= (3,4):
        raise
    asyncio = None

from concurrent.futures import CancelledError
from zmq.tests import BaseZMQTestCase, SkipTest
from zmq.tests.test_auth import TestThreadAuthentication


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

    @mark.skipif(not hasattr(zmq, 'RCVTIMEO'), reason="requires RCVTIMEO")
    def test_recv_timeout(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            b.rcvtimeo = 100
            f1 = b.recv()
            b.rcvtimeo = 1000
            f2 = b.recv_multipart()
            with self.assertRaises(zmq.Again):
                yield from f1
            yield from a.send_multipart([b'hi', b'there'])
            recvd = yield from f2
            assert f2.done()
            self.assertEqual(recvd, [b'hi', b'there'])
        self.loop.run_until_complete(test())

    @mark.skipif(not hasattr(zmq, 'SNDTIMEO'), reason="requires SNDTIMEO")
    def test_send_timeout(self):
        @asyncio.coroutine
        def test():
            s = self.socket(zmq.PUSH)
            s.sndtimeo = 100
            with self.assertRaises(zmq.Again):
                yield from s.send(b'not going anywhere')
        self.loop.run_until_complete(test())

    def test_recv_string(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_string()
            assert not f.done()
            msg = u('πøøπ')
            yield from a.send_string(msg)
            recvd = yield from f
            assert f.done()
            self.assertEqual(f.result(), msg)
            self.assertEqual(recvd, msg)
        self.loop.run_until_complete(test())

    def test_recv_json(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_json()
            assert not f.done()
            obj = dict(a=5)
            yield from a.send_json(obj)
            recvd = yield from f
            assert f.done()
            self.assertEqual(f.result(), obj)
            self.assertEqual(recvd, obj)
        self.loop.run_until_complete(test())

    def test_recv_json_cancelled(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_json()
            assert not f.done()
            f.cancel()
            # cycle eventloop to allow cancel events to fire
            yield from asyncio.sleep(0)
            obj = dict(a=5)
            yield from a.send_json(obj)
            with pytest.raises(CancelledError):
                recvd = yield from f
            assert f.done()
            # give it a chance to incorrectly consume the event
            events = yield from b.poll(timeout=5)
            assert events
            yield from asyncio.sleep(0)
            # make sure cancelled recv didn't eat up event
            f = b.recv_json()
            recvd = yield from asyncio.wait_for(f, timeout=5)
            assert recvd == obj
        self.loop.run_until_complete(test())

    def test_recv_pyobj(self):
        @asyncio.coroutine
        def test():
            a, b = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = b.recv_pyobj()
            assert not f.done()
            obj = dict(a=5)
            yield from a.send_pyobj(obj)
            recvd = yield from f
            assert f.done()
            self.assertEqual(f.result(), obj)
            self.assertEqual(recvd, obj)
        self.loop.run_until_complete(test())

    def test_recv_dontwait(self):
        @asyncio.coroutine
        def test():
            push, pull = self.create_bound_pair(zmq.PUSH, zmq.PULL)
            f = pull.recv(zmq.DONTWAIT)
            with self.assertRaises(zmq.Again):
                yield from f
            yield from push.send(b'ping')
            yield from pull.poll() # ensure message will be waiting
            f = pull.recv(zmq.DONTWAIT)
            assert f.done()
            msg = yield from f
            self.assertEqual(msg, b'ping')
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

    def test_starvation(self):
        # shared namespace because closures around coroutines are weird
        ns = dict(
            send_count=0,
            sleep_count=0,
            stop=False,
        )
        @asyncio.coroutine
        def starve():
            pub = self.socket(zmq.PUB)
            pub.bind_to_random_port('tcp://127.0.0.1')
            while ns['sleep_count'] < 10:
                if ns['stop']:
                    break
                yield from pub.send(b'x')
                ns['send_count'] += 1
                if ns['sleep_count'] <= 1 and ns['send_count'] >= 1e5:
                    # starvation is probaby happening
                    self.fail("sent %i msgs before waking twice, assuming starvation" % ns['send_count'])
            pub.close()
        
        sleep_count = 0
        @asyncio.coroutine
        def dont_starve():
            for i in range(10):
                yield from asyncio.sleep(0.1)
                ns['sleep_count'] += 1
            ns['stop'] = True

        self.loop.run_until_complete(asyncio.wait([ starve(), dont_starve() ]))
        assert ns['send_count'] >= 1000, "sent: %i" % ns['send_count']
        assert ns['sleep_count'] >= 10, "slept: %i" % ns['sleep_count']

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

    def test_poll_raw(self):
        @asyncio.coroutine
        def test():
            p = zaio.Poller()
            # make a pipe
            r, w = os.pipe()
            r = os.fdopen(r, 'rb')
            w = os.fdopen(w, 'wb')

            # POLLOUT
            p.register(r, zmq.POLLIN)
            p.register(w, zmq.POLLOUT)
            evts = yield from p.poll(timeout=1)
            evts = dict(evts)
            assert r.fileno() not in evts
            assert w.fileno() in evts
            assert evts[w.fileno()] == zmq.POLLOUT

            # POLLIN
            p.unregister(w)
            w.write(b'x')
            w.flush()
            evts = yield from p.poll(timeout=1000)
            evts = dict(evts)
            assert r.fileno() in evts
            assert evts[r.fileno()] == zmq.POLLIN
            assert r.read(1) == b'x'
            r.close()
            w.close()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(test())


class TestAsyncioAuthentication(TestThreadAuthentication):
    """Test authentication running in a asyncio task"""

    if asyncio is not None:
        Context = zaio.Context

    def shortDescription(self):
        """Rewrite doc strings from TestThreadAuthentication from
        'threaded' to 'asyncio'.
        """
        doc = self._testMethodDoc
        if doc:
            doc = doc.split("\n")[0].strip()
            if doc.startswith('threaded auth'):
                doc = doc.replace('threaded auth', 'asyncio auth')
        return doc

    def setUp(self):
        if asyncio is None:
            raise SkipTest()
        self.loop = zaio.ZMQEventLoop()
        asyncio.set_event_loop(self.loop)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.loop.close()

    def make_auth(self):
        return AsyncioAuthenticator(self.context)

    def can_connect(self, server, client):
        """Check if client can connect to server using tcp transport"""
        @asyncio.coroutine
        def go():
            result = False
            iface = 'tcp://127.0.0.1'
            port = server.bind_to_random_port(iface)
            client.connect("%s:%i" % (iface, port))
            msg = [b"Hello World"]
            yield from server.send_multipart(msg)
            if (yield from client.poll(1000)):
                rcvd_msg = yield from client.recv_multipart()
                self.assertEqual(rcvd_msg, msg)
                result = True
            return result
        return self.loop.run_until_complete(go())

    def _select_recv(self, multipart, socket, **kwargs):
        recv = socket.recv_multipart if multipart else socket.recv
        @asyncio.coroutine
        def coro():
            if not (yield from socket.poll(5000)):
                raise TimeoutError("Should have received a message")
            return (yield from recv(**kwargs))
        return self.loop.run_until_complete(coro())

