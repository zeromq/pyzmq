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

import os
import shutil
import zmq
import zmq.auth
from zmq.tests import (BaseZMQTestCase, SkipTest)


class TestAuthentication(BaseZMQTestCase):

    def setUp(self):
        if zmq.zmq_version_info() < (4,0):
            raise SkipTest("security is new in libzmq 4.0")
        super(TestAuthentication, self).setUp()

    def can_connect(self, server, client):
        """ Check if client can connect to server using tcp transport """
        result = False
        iface = 'tcp://127.0.0.1'
        port = server.bind_to_random_port(iface)
        client.connect("%s:%i" % (iface, port))
        msg = ["Hello World"]
        server.send_multipart(msg)
        poller = zmq.Poller()
        poller.register(client, zmq.POLLIN)
        socks = dict(poller.poll(100))
        if client in socks and socks[client] == zmq.POLLIN:
            rcvd_msg = client.recv_multipart()
            result = rcvd_msg == msg
            self.assertTrue(result)
        return result

    def test_null(self):
        """test NULL authentication """
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
        server.zap_domain = 'global'
        client = self.context.socket(zmq.PULL)
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

    def test_blacklist_whitelist(self):
        """ test Blacklist and Whitelist authentication """
        auth = zmq.auth.Authenticator(self.context)

        # Blacklist 127.0.0.1, connection should fail
        auth.deny('127.0.0.1')
        server = self.context.socket(zmq.PUSH)
        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet.
        server.zap_domain = 'global'
        client = self.context.socket(zmq.PULL)
        self.assertFalse(self.can_connect(server, client))
        client.close()
        server.close()

        # Whitelist 127.0.0.1, which overrides the blacklist, connection should pass"
        auth.allow('127.0.0.1')
        server = self.context.socket(zmq.PUSH)
        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet.
        server.zap_domain = 'global'
        client = self.context.socket(zmq.PULL)
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

        auth.stop()

    def test_plain(self):
        """test PLAIN authentication """
        auth = zmq.auth.Authenticator(self.context)

        # Try PLAIN authentication - without configuring server, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = 'admin'
        client.plain_password = 'Password'
        self.assertFalse(self.can_connect(server, client))
        client.close()
        server.close()

        # Try PLAIN authentication - with server configured, connection should pass
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = 'admin'
        client.plain_password = 'Password'
        auth.configure_plain(domain='*', passwords={'admin': 'Password'})
        self.assertTrue(self.can_connect(server, client))
        client.close()
        server.close()

        # Try PLAIN authentication - with bogus credentials, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = 'admin'
        client.plain_password = 'Bogus'
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
        """test CURVE authentication """
        auth = zmq.auth.Authenticator(self.context)

        # Create temporary CURVE keypairs for this test run. We create all keys in the
        # .certs directory and then move them into the appropriate private or public
        # directory.
        base_dir = os.path.dirname(os.path.abspath(__file__))
        keys_dir = os.path.join(base_dir, '.certs')
        public_keys_dir = os.path.join(base_dir, '.certs_public')
        secret_keys_dir = os.path.join(base_dir, '.certs_private')

        # Remove artefacts from a previous test run.
        if os.path.exists(keys_dir):
            shutil.rmtree(keys_dir)
        if os.path.exists(public_keys_dir):
            shutil.rmtree(public_keys_dir)
        if os.path.exists(secret_keys_dir):
            shutil.rmtree(secret_keys_dir)

        os.mkdir(keys_dir)
        os.mkdir(public_keys_dir)
        os.mkdir(secret_keys_dir)

        # create new keys in .certs dir
        server_public_file, server_secret_file = zmq.auth.create_certificates(keys_dir, "server")
        client_public_file, client_secret_file = zmq.auth.create_certificates(keys_dir, "client")

        # move public keys to appropriate directory
        for key_file in os.listdir(keys_dir):
            if key_file.endswith(".key"):
                shutil.move(os.path.join(keys_dir, key_file),
                            os.path.join(public_keys_dir, '.'))

        # move secret keys to appropriate directory
        for key_file in os.listdir(keys_dir):
            if key_file.endswith(".key_secret"):
                shutil.move(os.path.join(keys_dir, key_file),
                            os.path.join(secret_keys_dir, '.'))

        server_secret_file = os.path.join(secret_keys_dir, "server.key_secret")
        client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")

        server_public, server_secret = zmq.auth.load_certificate(server_secret_file)
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)

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
