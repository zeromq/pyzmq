# -*- coding: utf8 -*-
#-----------------------------------------------------------------------------
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import logging
import os
import shutil
import sys
import tempfile
from unittest import TestCase
import zmq
import zmq.auth
from zmq.eventloop import ioloop, zmqstream
from zmq.tests import (BaseZMQTestCase, SkipTest)


class TestThreadedAuthentication(BaseZMQTestCase):
    ''' Test authentication running in a thread '''

    def setUp(self):
        if zmq.zmq_version_info() < (4,0):
            raise SkipTest("security is new in libzmq 4.0")
        super(TestThreadedAuthentication, self).setUp()
        # silence auth module debug log output during test runs
        logger = logging.getLogger()
        self.original_log_level = logger.getEffectiveLevel()
        logger.setLevel(logging.DEBUG)

    def tearDown(self):
        # return log level to previous state
        logger = logging.getLogger()
        logger.setLevel(self.original_log_level)

    def can_connect(self, server, client):
        """ Check if client can connect to server using tcp transport """
        result = False
        iface = 'tcp://127.0.0.1'
        port = server.bind_to_random_port(iface)
        client.connect("%s:%i" % (iface, port))
        msg = [b"Hello World"]
        server.send_multipart(msg)
        poller = zmq.Poller()
        poller.register(client, zmq.POLLIN)
        socks = dict(poller.poll(100))
        if client in socks and socks[client] == zmq.POLLIN:
            rcvd_msg = client.recv_multipart()
            self.assertEqual(rcvd_msg, msg)
            result = True
        return result

    def test_null(self):
        """test threaded auth - NULL"""
        # A default NULL connection should always succeed, and not
        # go through our authentication infrastructure at all.
        server = self.context.socket(zmq.PUSH)
        client = self.context.socket(zmq.PULL)
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet. The client connection
        # should still be allowed.
        server = self.context.socket(zmq.PUSH)
        server.zap_domain = b'global'
        client = self.context.socket(zmq.PULL)
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

    def test_blacklist_whitelist(self):
        """test threaded auth - Blacklist and Whitelist"""
        auth = zmq.auth.ThreadedAuthenticator(self.context)
        auth.start()

        # Blacklist 127.0.0.1, connection should fail
        auth.deny('127.0.0.1')
        server = self.context.socket(zmq.PUSH)
        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet.
        server.zap_domain = b'global'
        client = self.context.socket(zmq.PULL)
        self.assertFalse(self.can_connect(server, client))
        client.close()
        server.close()

        # Whitelist 127.0.0.1, which overrides the blacklist, connection should pass"
        auth.allow('127.0.0.1')
        server = self.context.socket(zmq.PUSH)
        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet.
        server.zap_domain = b'global'
        client = self.context.socket(zmq.PULL)
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

        auth.stop()

    def test_plain(self):
        """test threaded auth - PLAIN"""
        auth = zmq.auth.ThreadedAuthenticator(self.context)
        auth.start()

        # Try PLAIN authentication - without configuring server, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = b'admin'
        client.plain_password = b'Password'
        self.assertFalse(self.can_connect(server, client))
        client.close()
        server.close()

        # Try PLAIN authentication - with server configured, connection should pass
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = b'admin'
        client.plain_password = b'Password'
        auth.configure_plain(domain='*', passwords={'admin': 'Password'})
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

        # Try PLAIN authentication - with bogus credentials, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = b'admin'
        client.plain_password = b'Bogus'
        self.assertFalse(self.can_connect(server, client))
        client.close()
        server.close()

        # Remove authenticator and check that a normal connection works
        auth.stop()
        del auth

        server = self.context.socket(zmq.PUSH)
        client = self.context.socket(zmq.PULL)
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

    def test_curve(self):
        """test threaded auth - CURVE"""
        auth = zmq.auth.ThreadedAuthenticator(self.context)
        auth.start()

        # Create temporary CURVE keypairs for this test run. We create all keys in a
        # temp directory and then move them into the appropriate private or public
        # directory.

        base_dir = tempfile.mkdtemp()
        keys_dir = os.path.join(base_dir, 'certificates')
        public_keys_dir = os.path.join(base_dir, 'public_keys')
        secret_keys_dir = os.path.join(base_dir, 'private_keys')

        os.mkdir(keys_dir)
        os.mkdir(public_keys_dir)
        os.mkdir(secret_keys_dir)

        server_public_file, server_secret_file = zmq.auth.create_certificates(keys_dir, "server")
        client_public_file, client_secret_file = zmq.auth.create_certificates(keys_dir, "client")

        for key_file in os.listdir(keys_dir):
            if key_file.endswith(".key"):
                shutil.move(os.path.join(keys_dir, key_file),
                            os.path.join(public_keys_dir, '.'))

        for key_file in os.listdir(keys_dir):
            if key_file.endswith(".key_secret"):
                shutil.move(os.path.join(keys_dir, key_file),
                            os.path.join(secret_keys_dir, '.'))

        server_secret_file = os.path.join(secret_keys_dir, "server.key_secret")
        client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")

        server_public, server_secret = zmq.auth.load_certificate(server_secret_file)
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)

        auth.allow('127.0.0.1')

        #Try CURVE authentication - without configuring server, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        self.assertFalse(self.can_connect(server, client))
        client.close()
        server.close()

        #Try CURVE authentication - with server configured to CURVE_ALLOW_ANY, connection should pass
        auth.configure_curve(domain='*', location=zmq.auth.CURVE_ALLOW_ANY)
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

        # Try CURVE authentication - with server configured, connection should pass
        auth.configure_curve(domain='*', location=public_keys_dir)
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

        # Remove authenticator and check that a normal connection works
        auth.stop()
        del auth

        # Try connecting using NULL and no authentication enabled, connection should pass
        server = self.context.socket(zmq.PUSH)
        client = self.context.socket(zmq.PULL)
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

        shutil.rmtree(base_dir)


class TestIOLoopAuthentication(TestCase):
    ''' Test authentication running in ioloop '''

    def setUp(self):
        if zmq.zmq_version_info() < (4,0):
            raise SkipTest("security is new in libzmq 4.0")

        # silence auth module debug log output during test runs
        logger = logging.getLogger()
        self.original_log_level = logger.getEffectiveLevel()
        logger.setLevel(logging.DEBUG)

        self.test_result = True
        self.io_loop = ioloop.IOLoop()
        self.auth = None
        self.context = zmq.Context()
        self.server = self.context.socket(zmq.PUSH)
        self.client = self.context.socket(zmq.PULL)
        # Only need slow reconnect intervals for testing.
        self.client.reconnect_ivl = 1000
        self.pushstream = zmqstream.ZMQStream(self.server, self.io_loop)
        self.pullstream = zmqstream.ZMQStream(self.client, self.io_loop)


    def tearDown(self):
        if self.auth:
            self.auth.stop()
            self.auth = None
        self.io_loop.close()
        self.context.destroy()
        # return log level to previous state
        logger = logging.getLogger()
        logger.setLevel(self.original_log_level)

    def attempt_connection(self):
        """ Check if client can connect to server using tcp transport """
        iface = 'tcp://127.0.0.1'
        port = self.server.bind_to_random_port(iface)
        self.client.connect("%s:%i" % (iface, port))

    def send_msg(self):
        ''' Send a message from server to a client '''
        msg = [b"Hello World"]
        self.server.send_multipart(msg)

    def on_message_succeed(self, frames):
        ''' A message was received, as expected. '''
        if frames != [b"Hello World"]:
            self.test_result = "Unexpected message received"
        self.test_result = True
        self.io_loop.stop()

    def on_message_fail(self, frames):
        ''' A message was received, unexpectedly. '''
        self.test_result = 'Received messaged unexpectedly, security failed'
        self.io_loop.stop()

    def on_test_timeout_succeed(self):
        ''' Test timer expired, indicates test success '''
        self.test_result = True
        self.io_loop.stop()

    def on_test_timeout_fail(self):
        ''' Test timer expired, indicates test failure '''
        self.test_result = 'Test timed out'
        if self.io_loop is not None:
            self.io_loop.stop()

    def create_certs(self):
        ''' Create CURVE certificates for a test '''

        # Create temporary CURVE keypairs for this test run. We create all keys in a
        # temp directory and then move them into the appropriate private or public
        # directory.

        base_dir = tempfile.mkdtemp()
        keys_dir = os.path.join(base_dir, 'certificates')
        public_keys_dir = os.path.join(base_dir, 'public_keys')
        secret_keys_dir = os.path.join(base_dir, 'private_keys')

        os.mkdir(keys_dir)
        os.mkdir(public_keys_dir)
        os.mkdir(secret_keys_dir)

        server_public_file, server_secret_file = zmq.auth.create_certificates(keys_dir, "server")
        client_public_file, client_secret_file = zmq.auth.create_certificates(keys_dir, "client")

        for key_file in os.listdir(keys_dir):
            if key_file.endswith(".key"):
                shutil.move(os.path.join(keys_dir, key_file),
                            os.path.join(public_keys_dir, '.'))

        for key_file in os.listdir(keys_dir):
            if key_file.endswith(".key_secret"):
                shutil.move(os.path.join(keys_dir, key_file),
                            os.path.join(secret_keys_dir, '.'))

        return (base_dir, public_keys_dir, secret_keys_dir)

    def remove_certs(self, base_dir):
        ''' Remove certificates for a test '''
        shutil.rmtree(base_dir)

    def load_certs(self, secret_keys_dir):
        ''' Return server and client certificate keys '''
        server_secret_file = os.path.join(secret_keys_dir, "server.key_secret")
        client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")

        server_public, server_secret = zmq.auth.load_certificate(server_secret_file)
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)

        return server_public, server_secret, client_public, client_secret

    def test_none(self):
        ''' test ioloop auth - NONE'''
        # A default NULL connection should always succeed, and not
        # go through our authentication infrastructure at all.
        self.pullstream.on_recv(self.on_message_succeed)
        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_fail)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)

    def test_null(self):
        """test ioloop auth - NULL"""
        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet. The client connection
        # should still be allowed.
        self.server.zap_domain = b'global'
        self.pullstream.on_recv(self.on_message_succeed)

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_fail)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)

    def test_blacklist(self):
        """ test ioloop auth - Blacklist"""

        self.auth = zmq.auth.IOLoopAuthenticator(self.context, io_loop=self.io_loop)
        self.auth.start()

        # Blacklist 127.0.0.1, connection should fail
        self.auth.deny('127.0.0.1')

        self.server.zap_domain = b'global'
        # The test should fail if a msg is received
        self.pullstream.on_recv(self.on_message_fail)

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_succeed)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)


    def test_whitelist(self):
        """ test ioloop auth - Whitelist"""

        self.auth = zmq.auth.IOLoopAuthenticator(self.context, io_loop=self.io_loop)
        self.auth.start()

        # Whitelist 127.0.0.1, which overrides the blacklist, connection should pass"
        self.auth.allow('127.0.0.1')

        self.server.setsockopt(zmq.ZAP_DOMAIN, b'global')
        self.pullstream.on_recv(self.on_message_succeed)

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_fail)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)


    def test_plain_unconfigured_server(self):
        """test ioloop auth - PLAIN, unconfigured server"""
        auth = zmq.auth.IOLoopAuthenticator(self.context, io_loop=self.io_loop)
        auth.start()

        self.client.plain_username = b'admin'
        self.client.plain_password = b'Password'
        self.pullstream.on_recv(self.on_message_fail)
        # Try PLAIN authentication - without configuring server, connection should fail
        self.server.plain_server = True

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_succeed)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)

    def test_plain_configured_server(self):
        """test ioloop auth - PLAIN, configured server"""
        auth = zmq.auth.IOLoopAuthenticator(self.context, io_loop=self.io_loop)
        auth.start()
        auth.configure_plain(domain='*', passwords={'admin': 'Password'})

        self.client.plain_username = b'admin'
        self.client.plain_password = b'Password'
        self.pullstream.on_recv(self.on_message_succeed)
        # Try PLAIN authentication - with server configured, connection should pass
        self.server.plain_server = True

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_fail)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)

    def test_plain_bogus_credentials(self):
        """test ioloop auth - PLAIN, bogus credentials"""
        auth = zmq.auth.IOLoopAuthenticator(self.context, io_loop=self.io_loop)
        auth.start()
        auth.configure_plain(domain='*', passwords={'admin': 'Password'})

        self.client.plain_username = b'admin'
        self.client.plain_password = b'Bogus'
        self.pullstream.on_recv(self.on_message_fail)
        # Try PLAIN authentication - with server configured, connection should pass
        self.server.plain_server = True

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_succeed)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)

    def test_curve_unconfigured_server(self):
        """test ioloop auth - CURVE, unconfigured server"""
        base_dir, public_keys_dir, secret_keys_dir = self.create_certs()
        certs = self.load_certs(secret_keys_dir)
        server_public, server_secret, client_public, client_secret = certs

        auth = zmq.auth.IOLoopAuthenticator(self.context, io_loop=self.io_loop)
        auth.start()
        auth.allow('127.0.0.1')

        self.server.curve_publickey = server_public
        self.server.curve_secretkey = server_secret
        self.server.curve_server = True

        self.client.curve_publickey = client_public
        self.client.curve_secretkey = client_secret
        self.client.curve_serverkey = server_public
        self.pullstream.on_recv(self.on_message_fail)

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_succeed)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)

        self.remove_certs(base_dir)

    def test_curve_allow_any(self):
        """test ioloop auth - CURVE, CURVE_ALLOW_ANY"""
        base_dir, public_keys_dir, secret_keys_dir = self.create_certs()
        certs = self.load_certs(secret_keys_dir)
        server_public, server_secret, client_public, client_secret = certs

        auth = zmq.auth.IOLoopAuthenticator(self.context, io_loop=self.io_loop)
        auth.start()
        auth.allow('127.0.0.1')
        auth.configure_curve(domain='*', location=zmq.auth.CURVE_ALLOW_ANY)

        self.server.curve_publickey = server_public
        self.server.curve_secretkey = server_secret
        self.server.curve_server = True

        self.client.curve_publickey = client_public
        self.client.curve_secretkey = client_secret
        self.client.curve_serverkey = server_public
        self.pullstream.on_recv(self.on_message_succeed)

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_fail)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)

        self.remove_certs(base_dir)

    def test_curve_configured_server(self):
        """test ioloop auth - CURVE, configured server"""

        auth = zmq.auth.IOLoopAuthenticator(self.context, io_loop=self.io_loop)
        auth.start()
        auth.allow('127.0.0.1')

        base_dir, public_keys_dir, secret_keys_dir = self.create_certs()
        certs = self.load_certs(secret_keys_dir)
        server_public, server_secret, client_public, client_secret = certs

        auth.configure_curve(domain='*', location=public_keys_dir)

        self.server.curve_publickey = server_public
        self.server.curve_secretkey = server_secret
        self.server.curve_server = True

        self.client.curve_publickey = client_public
        self.client.curve_secretkey = client_secret
        self.client.curve_serverkey = server_public
        self.pullstream.on_recv(self.on_message_succeed)

        t = self.io_loop.time()
        step1 = self.io_loop.add_timeout(t + .1, self.attempt_connection)
        step2 = self.io_loop.add_timeout(t + .2, self.send_msg)
        # Timeout the test so the test case can complete even if no message
        # is received.
        timeout = self.io_loop.add_timeout(t + .5, self.on_test_timeout_fail)

        self.io_loop.start()

        if not (self.test_result == True):
            self.fail(self.test_result)

        self.remove_certs(base_dir)
