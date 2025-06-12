# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import time

import pytest

import zmq
from zmq_test_utils import BaseZMQTestCase, skip_pypy

pytestmark = pytest.mark.skipif(not zmq.DRAFT_API, reason="draft api unavailable")


class TestDraftSockets(BaseZMQTestCase):
    @skip_pypy
    def test_client_server(self):
        client, server = self.create_bound_pair(zmq.CLIENT, zmq.SERVER)
        client.send(b'request')
        msg = self.recv(server, copy=False)
        assert msg.routing_id is not None
        server.send(b'reply', routing_id=msg.routing_id)
        reply = self.recv(client)
        assert reply == b'reply'

    def test_client_server_frame(self):
        client, server = self.create_bound_pair(zmq.CLIENT, zmq.SERVER)
        client.send(b'request')
        msg = self.recv(server, copy=False)
        server.send(msg)
        reply = self.recv(client)
        assert reply == b'request'

    @skip_pypy
    def test_radio_dish(self):
        dish, radio = self.create_bound_pair(zmq.DISH, zmq.RADIO)
        dish.rcvtimeo = 250
        group = 'mygroup'
        dish.join(group)
        received_count = 0
        received = set()
        sent = set()
        for i in range(10):
            msg = str(i).encode('ascii')
            sent.add(msg)
            radio.send(msg, group=group)
            try:
                recvd = dish.recv()
            except zmq.Again:
                time.sleep(0.1)
            else:
                received.add(recvd)
                received_count += 1
        # assert that we got *something*
        assert len(received.intersection(sent)) >= 5


def test_draft_fd():
    if zmq.zmq_version_info() < (4, 3, 2):
        pytest.skip("requires libzmq 4.3.2 for zmq_poller_fd")
    with zmq.Context() as ctx, ctx.socket(zmq.SERVER) as s:
        fd = s.FD
        assert isinstance(fd, int)
        fd_2 = s.get(zmq.FD)
        assert fd_2 == fd
