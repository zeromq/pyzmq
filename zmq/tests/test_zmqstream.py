# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import asyncio
import logging
from functools import partial
from unittest import TestCase

import pytest

import zmq

try:
    import tornado
    from tornado import gen, ioloop

    from zmq.eventloop import zmqstream
except ImportError:
    tornado = None  # type: ignore

caplog = None


@pytest.fixture
def get_caplog(caplog):
    globals()["caplog"] = caplog


@pytest.mark.usefixtures("get_caplog")
class TestZMQStream(TestCase):
    def setUp(self):
        if tornado is None:
            pytest.skip()
        self._timeout_task = None
        self.context = zmq.Context()
        self.loop = ioloop.IOLoop(make_current=False)
        if tornado and tornado.version_info < (5,):
            self.loop.make_current()

        async def _make_sockets():
            self.push = zmqstream.ZMQStream(self.context.socket(zmq.PUSH))
            self.pull = zmqstream.ZMQStream(self.context.socket(zmq.PULL))

        self.loop.run_sync(_make_sockets)
        port = self.push.bind_to_random_port('tcp://127.0.0.1')
        self.pull.connect('tcp://127.0.0.1:%i' % port)
        self.stream = self.push

    def tearDown(self):
        if self._timeout_task:
            self._timeout_task.cancel()

            async def wait():
                await gen.with_timeout(self.loop.time() + 1, self._timeout_task)

            self.loop.run_sync(wait)
        self.loop.close(all_fds=True)
        self.context.term()

    def run_until_timeout(self, timeout=10):
        timed_out = []

        async def sleep_timeout():
            try:
                await gen.sleep(timeout)
            except asyncio.CancelledError:
                return
            timed_out[:] = ['timed out']
            self.loop.stop()

        def make_timeout_task():
            if tornado.version_info < (5,):
                self.loop.add_callback(sleep_timeout)
            else:
                self._timeout_task = asyncio.ensure_future(sleep_timeout())

        self.loop.run_sync(make_timeout_task)
        self.loop.start()
        assert not timed_out

    def test_callable_check(self):
        """Ensure callable check works (py3k)."""

        self.stream.on_send(lambda *args: None)
        self.stream.on_recv(lambda *args: None)
        self.assertRaises(AssertionError, self.stream.on_recv, 1)
        self.assertRaises(AssertionError, self.stream.on_send, 1)
        self.assertRaises(AssertionError, self.stream.on_recv, zmq)

    def test_on_recv_basic(self):
        sent = [b'basic']

        def callback(msg):
            assert msg == sent
            self.loop.stop()

        self.loop.run_sync(partial(self.push.send_multipart, sent))
        self.pull.on_recv(callback)
        self.run_until_timeout()

    def test_on_recv_wake(self):
        sent = [b'wake']

        def callback(msg):
            assert msg == sent
            self.loop.stop()

        self.pull.on_recv(callback)
        self.loop.call_later(0.5, lambda: self.push.send_multipart(sent))
        self.run_until_timeout()

    def test_on_recv_async(self):
        sent = [b'wake']

        async def callback(msg):
            assert msg == sent
            self.loop.stop()

        self.pull.on_recv(callback)
        self.loop.call_later(0.5, lambda: self.push.send_multipart(sent))
        self.run_until_timeout()

    def test_on_recv_async_error(self):
        sent = [b'wake']

        async def callback(msg):
            ioloop.IOLoop.current().call_later(0.5, lambda: self.loop.stop())
            assert msg == sent
            1 / 0

        self.pull.on_recv(callback)
        self.loop.call_later(0.5, lambda: self.push.send_multipart(sent))
        with caplog.at_level(logging.ERROR, logger=zmqstream.gen_log.name):
            self.run_until_timeout()

        messages = [
            x.message
            for x in caplog.get_records("call")
            if x.name == zmqstream.gen_log.name
        ]
        assert "Uncaught exception in ZMQStream callback" in "\n".join(messages)
