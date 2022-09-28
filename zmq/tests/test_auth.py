# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import asyncio
import logging
import os
import shutil
import warnings

import pytest

import zmq
import zmq.asyncio
import zmq.auth
from zmq.tests import SkipTest, skip_pypy

try:
    import tornado
except ImportError:
    tornado = None


@pytest.fixture
def create_certs(tmpdir):
    """Create CURVE certificates for a test"""

    # Create temporary CURVE key pairs for this test run. We create all keys in a
    # temp directory and then move them into the appropriate private or public
    # directory.
    base_dir = str(tmpdir.join("certs").mkdir())
    keys_dir = os.path.join(base_dir, "certificates")
    public_keys_dir = os.path.join(base_dir, 'public_keys')
    secret_keys_dir = os.path.join(base_dir, 'private_keys')

    os.mkdir(keys_dir)
    os.mkdir(public_keys_dir)
    os.mkdir(secret_keys_dir)

    server_public_file, server_secret_file = zmq.auth.create_certificates(
        keys_dir, "server"
    )
    client_public_file, client_secret_file = zmq.auth.create_certificates(
        keys_dir, "client"
    )
    for key_file in os.listdir(keys_dir):
        if key_file.endswith(".key"):
            shutil.move(
                os.path.join(keys_dir, key_file), os.path.join(public_keys_dir, '.')
            )

    for key_file in os.listdir(keys_dir):
        if key_file.endswith(".key_secret"):
            shutil.move(
                os.path.join(keys_dir, key_file), os.path.join(secret_keys_dir, '.')
            )

    return (public_keys_dir, secret_keys_dir)


def load_certs(secret_keys_dir):
    """Return server and client certificate keys"""
    server_secret_file = os.path.join(secret_keys_dir, "server.key_secret")
    client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")

    server_public, server_secret = zmq.auth.load_certificate(server_secret_file)
    client_public, client_secret = zmq.auth.load_certificate(client_secret_file)

    return server_public, server_secret, client_public, client_secret


@pytest.fixture
def public_keys_dir(create_certs):
    public_keys_dir, secret_keys_dir = create_certs
    return public_keys_dir


@pytest.fixture
def secret_keys_dir(create_certs):
    public_keys_dir, secret_keys_dir = create_certs
    return secret_keys_dir


@pytest.fixture
def certs(secret_keys_dir):
    return load_certs(secret_keys_dir)


@pytest.fixture
async def _async_setup(request):
    """pytest doesn't support async setup/teardown"""
    instance = request.instance
    await instance.async_setup()


@pytest.mark.usefixtures("_async_setup")
class AuthTest:
    auth = None

    async def async_setup(self):
        self.context = zmq.asyncio.Context()
        if zmq.zmq_version_info() < (4, 0):
            raise SkipTest("security is new in libzmq 4.0")
        try:
            zmq.curve_keypair()
        except zmq.ZMQError:
            raise SkipTest("security requires libzmq to have curve support")
        # enable debug logging while we run tests
        logging.getLogger('zmq.auth').setLevel(logging.DEBUG)
        self.auth = self.make_auth()
        await self.start_auth()

    def teardown(self):
        if self.auth:
            self.auth.stop()
            self.auth = None
        self.context.destroy()

    def make_auth(self):
        raise NotImplementedError()

    async def start_auth(self):
        self.auth.start()

    async def can_connect(self, server, client, timeout=1000):
        """Check if client can connect to server using tcp transport"""
        result = False
        iface = 'tcp://127.0.0.1'
        port = server.bind_to_random_port(iface)
        client.connect("%s:%i" % (iface, port))
        msg = [b"Hello World"]
        # run poll on server twice
        # to flush spurious events
        await server.poll(100, zmq.POLLOUT)

        if await server.poll(timeout, zmq.POLLOUT):
            try:
                await server.send_multipart(msg, zmq.NOBLOCK)
            except zmq.Again:
                warnings.warn("server set POLLOUT, but cannot send", RuntimeWarning)
                return False
        else:
            return False

        if await client.poll(timeout):
            try:
                rcvd_msg = await client.recv_multipart(zmq.NOBLOCK)
            except zmq.Again:
                warnings.warn("client set POLLIN, but cannot recv", RuntimeWarning)
            else:
                assert rcvd_msg == msg
                result = True
        return result

    async def test_null(self):
        """threaded auth - NULL"""
        # A default NULL connection should always succeed, and not
        # go through our authentication infrastructure at all.
        self.auth.stop()
        self.auth = None

        # use a new context, so ZAP isn't inherited
        self.context.destroy()
        self.context = zmq.asyncio.Context()

        server = self.context.socket(zmq.PUSH)
        client = self.context.socket(zmq.PULL)
        assert await self.can_connect(server, client)

        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet. The client connection
        # should still be allowed.
        server = self.context.socket(zmq.PUSH)
        server.zap_domain = b'global'
        client = self.context.socket(zmq.PULL)
        assert await self.can_connect(server, client)

    async def test_blacklist(self):
        """threaded auth - Blacklist"""
        # Blacklist 127.0.0.1, connection should fail
        self.auth.deny('127.0.0.1')
        server = self.context.socket(zmq.PUSH)
        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet.
        server.zap_domain = b'global'
        client = self.context.socket(zmq.PULL)
        assert not await self.can_connect(server, client, timeout=100)

    async def test_whitelist(self):
        """threaded auth - Whitelist"""
        # Whitelist 127.0.0.1, connection should pass"
        self.auth.allow('127.0.0.1')
        server = self.context.socket(zmq.PUSH)
        # By setting a domain we switch on authentication for NULL sockets,
        # though no policies are configured yet.
        server.zap_domain = b'global'
        client = self.context.socket(zmq.PULL)
        assert await self.can_connect(server, client)

    async def test_plain(self):
        """threaded auth - PLAIN"""

        # Try PLAIN authentication - without configuring server, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = b'admin'
        client.plain_password = b'Password'
        assert not await self.can_connect(server, client, timeout=100)

        # Try PLAIN authentication - with server configured, connection should pass
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = b'admin'
        client.plain_password = b'Password'
        self.auth.configure_plain(domain='*', passwords={'admin': 'Password'})
        assert await self.can_connect(server, client)

        # Try PLAIN authentication - with bogus credentials, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.plain_server = True
        client = self.context.socket(zmq.PULL)
        client.plain_username = b'admin'
        client.plain_password = b'Bogus'
        assert not await self.can_connect(server, client, timeout=100)

        # Remove authenticator and check that a normal connection works
        self.auth.stop()
        self.auth = None

        server = self.context.socket(zmq.PUSH)
        client = self.context.socket(zmq.PULL)
        assert await self.can_connect(server, client)
        client.close()
        server.close()

    async def test_curve(self, certs, public_keys_dir):
        """threaded auth - CURVE"""
        self.auth.allow('127.0.0.1')
        server_public, server_secret, client_public, client_secret = certs

        # Try CURVE authentication - without configuring server, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert not await self.can_connect(server, client, timeout=100)

        # Try CURVE authentication - with server configured to CURVE_ALLOW_ANY, connection should pass
        self.auth.configure_curve(domain='*', location=zmq.auth.CURVE_ALLOW_ANY)
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert await self.can_connect(server, client)

        # Try CURVE authentication - with server configured, connection should pass
        self.auth.configure_curve(domain='*', location=public_keys_dir)
        server = self.context.socket(zmq.PULL)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PUSH)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert await self.can_connect(client, server)

        # Remove authenticator and check that a normal connection works
        self.auth.stop()
        self.auth = None

        # Try connecting using NULL and no authentication enabled, connection should pass
        server = self.context.socket(zmq.PUSH)
        client = self.context.socket(zmq.PULL)
        assert await self.can_connect(server, client)

    async def test_curve_callback(self, certs):
        """threaded auth - CURVE with callback authentication"""
        self.auth.allow('127.0.0.1')
        server_public, server_secret, client_public, client_secret = certs

        # Try CURVE authentication - without configuring server, connection should fail
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert not await self.can_connect(server, client, timeout=100)

        # Try CURVE authentication - with callback authentication configured, connection should pass

        class CredentialsProvider:
            def __init__(self):
                self.client = client_public

            def callback(self, domain, key):
                if key == self.client:
                    return True
                else:
                    return False

        provider = CredentialsProvider()
        self.auth.configure_curve_callback(credentials_provider=provider)
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert await self.can_connect(server, client, timeout=100)

        # Try CURVE authentication - with async callback authentication configured, connection should pass

        class AsyncCredentialsProvider:
            def __init__(self):
                self.client = client_public

            async def callback(self, domain, key):
                await asyncio.sleep(0.1)
                if key == self.client:
                    return True
                else:
                    return False

        provider = AsyncCredentialsProvider()
        self.auth.configure_curve_callback(credentials_provider=provider)
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert await self.can_connect(server, client)

        # Try CURVE authentication - with callback authentication configured with wrong key, connection should not pass

        class WrongCredentialsProvider:
            def __init__(self):
                self.client = "WrongCredentials"

            def callback(self, domain, key):
                if key == self.client:
                    return True
                else:
                    return False

        provider = WrongCredentialsProvider()
        self.auth.configure_curve_callback(credentials_provider=provider)
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert not await self.can_connect(server, client, timeout=100)

        # Try CURVE authentication - with async callback authentication configured with wrong key, connection should not pass

        class WrongAsyncCredentialsProvider:
            def __init__(self):
                self.client = "WrongCredentials"

            async def callback(self, domain, key):
                await asyncio.sleep(0.1)
                if key == self.client:
                    return True
                else:
                    return False

        provider = WrongAsyncCredentialsProvider()
        self.auth.configure_curve_callback(credentials_provider=provider)
        server = self.context.socket(zmq.PUSH)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PULL)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert not await self.can_connect(server, client)

    @skip_pypy
    async def test_curve_user_id(self, certs, public_keys_dir):
        """threaded auth - CURVE"""
        self.auth.allow('127.0.0.1')
        server_public, server_secret, client_public, client_secret = certs

        self.auth.configure_curve(domain='*', location=public_keys_dir)
        server = self.context.socket(zmq.PULL)
        server.curve_publickey = server_public
        server.curve_secretkey = server_secret
        server.curve_server = True
        client = self.context.socket(zmq.PUSH)
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        assert await self.can_connect(client, server)

        # test default user-id map
        await client.send(b'test')
        msg = await server.recv(copy=False)
        assert msg.bytes == b'test'
        try:
            user_id = msg.get('User-Id')
        except zmq.ZMQVersionError:
            pass
        else:
            assert user_id == client_public.decode("utf8")

        # test custom user-id map
        self.auth.curve_user_id = lambda client_key: 'custom'

        client2 = self.context.socket(zmq.PUSH)
        client2.curve_publickey = client_public
        client2.curve_secretkey = client_secret
        client2.curve_serverkey = server_public
        assert await self.can_connect(client2, server)

        await client2.send(b'test2')
        msg = await server.recv(copy=False)
        assert msg.bytes == b'test2'
        try:
            user_id = msg.get('User-Id')
        except zmq.ZMQVersionError:
            pass
        else:
            assert user_id == 'custom'


class TestThreadAuthentication(AuthTest):
    """Test authentication running in a thread"""

    def make_auth(self):
        from zmq.auth.thread import ThreadAuthenticator

        return ThreadAuthenticator(self.context)


class TestAsyncioAuthentication(AuthTest):
    """Test authentication running in a thread"""

    def make_auth(self):
        from zmq.auth.asyncio import AsyncioAuthenticator

        return AsyncioAuthenticator(self.context)


@pytest.mark.usefixtures("io_loop")
@pytest.mark.skipif(tornado is None, reason="requires tornado")
class TestIOLoopAuthentication(AuthTest):
    """Test authentication running in a thread"""

    def make_auth(self):
        from zmq.auth.ioloop import IOLoopAuthenticator

        return IOLoopAuthenticator(self.context)
