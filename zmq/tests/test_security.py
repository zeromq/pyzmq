"""Test libzmq security (libzmq >= 3.3.0)"""
# -*- coding: utf8 -*-

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import os
from threading import Thread

import zmq
from zmq.tests import (
    BaseZMQTestCase, SkipTest, PYPY
)
from zmq.utils import z85


USER = b"admin"
PASS = b"password"

class TestSecurity(BaseZMQTestCase):
    
    def setUp(self):
        if zmq.zmq_version_info() < (4,0):
            raise SkipTest("security is new in libzmq 4.0")
        try:
            zmq.curve_keypair()
        except zmq.ZMQError:
            raise SkipTest("security requires libzmq to be linked against libsodium")
        super(TestSecurity, self).setUp()
    
    
    def zap_handler(self):
        socket = self.context.socket(zmq.REP)
        socket.bind("inproc://zeromq.zap.01")
        try:
            msg = self.recv_multipart(socket)

            version, sequence, domain, address, identity, mechanism = msg[:6]
            if mechanism == b'PLAIN':
                username, password = msg[6:]
            elif mechanism == b'CURVE':
                key = msg[6]

            self.assertEqual(version, b"1.0")
            self.assertEqual(identity, b"IDENT")
            reply = [version, sequence]
            if mechanism == b'CURVE' or \
                (mechanism == b'PLAIN' and username == USER and password == PASS) or \
                (mechanism == b'NULL'):
                reply.extend([
                    b"200",
                    b"OK",
                    b"anonymous",
                    b"\5Hello\0\0\0\5World",
                ])
            else:
                reply.extend([
                    b"400",
                    b"Invalid username or password",
                    b"",
                    b"",
                ])
            socket.send_multipart(reply)
        finally:
            socket.close()
    
    def start_zap(self):
        self.zap_thread = Thread(target=self.zap_handler)
        self.zap_thread.start()
    
    def stop_zap(self):
        self.zap_thread.join()

    def bounce(self, server, client, test_metadata=True):
        msg = [os.urandom(64), os.urandom(64)]
        client.send_multipart(msg)
        frames = self.recv_multipart(server, copy=False)
        recvd = list(map(lambda x: x.bytes, frames))

        try:
            if test_metadata and not PYPY:
                for frame in frames:
                    self.assertEqual(frame.get('User-Id'), 'anonymous')
                    self.assertEqual(frame.get('Hello'), 'World')
                    self.assertEqual(frame['Socket-Type'], 'DEALER')
        except zmq.ZMQVersionError:
            pass

        self.assertEqual(recvd, msg)
        server.send_multipart(recvd)
        msg2 = self.recv_multipart(client)
        self.assertEqual(msg2, msg)
    
    def test_null(self):
        """test NULL (default) security"""
        server = self.socket(zmq.DEALER)
        client = self.socket(zmq.DEALER)
        self.assertEqual(client.MECHANISM, zmq.NULL)
        self.assertEqual(server.mechanism, zmq.NULL)
        self.assertEqual(client.plain_server, 0)
        self.assertEqual(server.plain_server, 0)
        iface = 'tcp://127.0.0.1'
        port = server.bind_to_random_port(iface)
        client.connect("%s:%i" % (iface, port))
        self.bounce(server, client, False)

    def test_plain(self):
        """test PLAIN authentication"""
        server = self.socket(zmq.DEALER)
        server.identity = b'IDENT'
        client = self.socket(zmq.DEALER)
        self.assertEqual(client.plain_username, b'')
        self.assertEqual(client.plain_password, b'')
        client.plain_username = USER
        client.plain_password = PASS
        self.assertEqual(client.getsockopt(zmq.PLAIN_USERNAME), USER)
        self.assertEqual(client.getsockopt(zmq.PLAIN_PASSWORD), PASS)
        self.assertEqual(client.plain_server, 0)
        self.assertEqual(server.plain_server, 0)
        server.plain_server = True
        self.assertEqual(server.mechanism, zmq.PLAIN)
        self.assertEqual(client.mechanism, zmq.PLAIN)
        
        assert not client.plain_server
        assert server.plain_server
        
        self.start_zap()
        
        iface = 'tcp://127.0.0.1'
        port = server.bind_to_random_port(iface)
        client.connect("%s:%i" % (iface, port))
        self.bounce(server, client)
        self.stop_zap()

    def skip_plain_inauth(self):
        """test PLAIN failed authentication"""
        server = self.socket(zmq.DEALER)
        server.identity = b'IDENT'
        client = self.socket(zmq.DEALER)
        self.sockets.extend([server, client])
        client.plain_username = USER
        client.plain_password = b'incorrect'
        server.plain_server = True
        self.assertEqual(server.mechanism, zmq.PLAIN)
        self.assertEqual(client.mechanism, zmq.PLAIN)
        
        self.start_zap()
        
        iface = 'tcp://127.0.0.1'
        port = server.bind_to_random_port(iface)
        client.connect("%s:%i" % (iface, port))
        client.send(b'ping')
        server.rcvtimeo = 250
        self.assertRaisesErrno(zmq.EAGAIN, server.recv)
        self.stop_zap()
    
    def test_keypair(self):
        """test curve_keypair"""
        try:
            public, secret = zmq.curve_keypair()
        except zmq.ZMQError:
            raise SkipTest("CURVE unsupported")
        
        self.assertEqual(type(secret), bytes)
        self.assertEqual(type(public), bytes)
        self.assertEqual(len(secret), 40)
        self.assertEqual(len(public), 40)
        
        # verify that it is indeed Z85
        bsecret, bpublic = [ z85.decode(key) for key in (public, secret) ]
        self.assertEqual(type(bsecret), bytes)
        self.assertEqual(type(bpublic), bytes)
        self.assertEqual(len(bsecret), 32)
        self.assertEqual(len(bpublic), 32)
        
    
    def test_curve(self):
        """test CURVE encryption"""
        server = self.socket(zmq.DEALER)
        server.identity = b'IDENT'
        client = self.socket(zmq.DEALER)
        self.sockets.extend([server, client])
        try:
            server.curve_server = True
        except zmq.ZMQError as e:
            # will raise EINVAL if not linked against libsodium
            if e.errno == zmq.EINVAL:
                raise SkipTest("CURVE unsupported")
        
        server_public, server_secret = zmq.curve_keypair()
        client_public, client_secret = zmq.curve_keypair()
        
        server.curve_secretkey = server_secret
        server.curve_publickey = server_public
        client.curve_serverkey = server_public
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        
        self.assertEqual(server.mechanism, zmq.CURVE)
        self.assertEqual(client.mechanism, zmq.CURVE)
        
        self.assertEqual(server.get(zmq.CURVE_SERVER), True)
        self.assertEqual(client.get(zmq.CURVE_SERVER), False)
        
        self.start_zap()
        
        iface = 'tcp://127.0.0.1'
        port = server.bind_to_random_port(iface)
        client.connect("%s:%i" % (iface, port))
        self.bounce(server, client)
        self.stop_zap()
        
