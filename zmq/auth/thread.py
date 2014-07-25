"""ZAP Authenticator in a Python Thread.

.. versionadded:: 14.1
"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import logging
from threading import Thread

import zmq
from zmq.utils import jsonapi
from zmq.utils.strtypes import bytes, unicode, b, u

from .base import Authenticator

class AuthenticationThread(Thread):
    """A Thread for running a zmq Authenticator
    
    This is run in the background by ThreadedAuthenticator
    """

    def __init__(self, context, endpoint, encoding='utf-8', log=None):
        super(AuthenticationThread, self).__init__()
        self.context = context or zmq.Context.instance()
        self.encoding = encoding
        self.log = log = log or logging.getLogger('zmq.auth')
        self.authenticator = Authenticator(context, encoding=encoding, log=log)

        # create a socket to communicate back to main thread.
        self.pipe = context.socket(zmq.PAIR)
        self.pipe.linger = 1
        self.pipe.connect(endpoint)

    def run(self):
        """ Start the Authentication Agent thread task """
        self.authenticator.start()
        zap = self.authenticator.zap_socket
        poller = zmq.Poller()
        poller.register(self.pipe, zmq.POLLIN)
        poller.register(zap, zmq.POLLIN)
        while True:
            try:
                socks = dict(poller.poll())
            except zmq.ZMQError:
                break  # interrupted

            if self.pipe in socks and socks[self.pipe] == zmq.POLLIN:
                terminate = self._handle_pipe()
                if terminate:
                    break

            if zap in socks and socks[zap] == zmq.POLLIN:
                self._handle_zap()

        self.pipe.close()
        self.authenticator.stop()

    def _handle_zap(self):
        """
        Handle a message from the ZAP socket.
        """
        msg = self.authenticator.zap_socket.recv_multipart()
        if not msg: return
        self.authenticator.handle_zap_message(msg)

    def _handle_pipe(self):
        """
        Handle a message from front-end API.
        """
        terminate = False

        # Get the whole message off the pipe in one go
        msg = self.pipe.recv_multipart()

        if msg is None:
            terminate = True
            return terminate

        command = msg[0]
        self.log.debug("auth received API command %r", command)

        if command == b'ALLOW':
            addresses = [u(m, self.encoding) for m in msg[1:]]
            try:
                self.authenticator.allow(*addresses)
            except Exception as e:
                self.log.exception("Failed to allow %s", addresses)

        elif command == b'DENY':
            addresses = [u(m, self.encoding) for m in msg[1:]]
            try:
                self.authenticator.deny(*addresses)
            except Exception as e:
                self.log.exception("Failed to deny %s", addresses)

        elif command == b'PLAIN':
            domain = u(msg[1], self.encoding)
            json_passwords = msg[2]
            self.authenticator.configure_plain(domain, jsonapi.loads(json_passwords))

        elif command == b'CURVE':
            # For now we don't do anything with domains
            domain = u(msg[1], self.encoding)

            # If location is CURVE_ALLOW_ANY, allow all clients. Otherwise
            # treat location as a directory that holds the certificates.
            location = u(msg[2], self.encoding)
            self.authenticator.configure_curve(domain, location)

        elif command == b'TERMINATE':
            terminate = True

        else:
            self.log.error("Invalid auth command from API: %r", command)

        return terminate

def _inherit_docstrings(cls):
    """inherit docstrings from Authenticator, so we don't duplicate them"""
    for name, method in cls.__dict__.items():
        if name.startswith('_'):
            continue
        upstream_method = getattr(Authenticator, name, None)
        if not method.__doc__:
            method.__doc__ = upstream_method.__doc__
    return cls

@_inherit_docstrings
class ThreadAuthenticator(object):
    """Run ZAP authentication in a background thread"""

    def __init__(self, context=None, encoding='utf-8', log=None):
        self.context = context or zmq.Context.instance()
        self.log = log
        self.encoding = encoding
        self.pipe = None
        self.pipe_endpoint = "inproc://{0}.inproc".format(id(self))
        self.thread = None

    def allow(self, *addresses):
        self.pipe.send_multipart([b'ALLOW'] + [b(a, self.encoding) for a in addresses])

    def deny(self, *addresses):
        self.pipe.send_multipart([b'DENY'] + [b(a, self.encoding) for a in addresses])

    def configure_plain(self, domain='*', passwords=None):
        self.pipe.send_multipart([b'PLAIN', b(domain, self.encoding), jsonapi.dumps(passwords or {})])

    def configure_curve(self, domain='*', location=''):
        domain = b(domain, self.encoding)
        location = b(location, self.encoding)
        self.pipe.send_multipart([b'CURVE', domain, location])

    def start(self):
        """Start the authentication thread"""
        # create a socket to communicate with auth thread.
        self.pipe = self.context.socket(zmq.PAIR)
        self.pipe.linger = 1
        self.pipe.bind(self.pipe_endpoint)
        self.thread = AuthenticationThread(self.context, self.pipe_endpoint, encoding=self.encoding, log=self.log)
        self.thread.start()

    def stop(self):
        """Stop the authentication thread"""
        if self.pipe:
            self.pipe.send(b'TERMINATE')
            if self.is_alive():
                self.thread.join()
            self.thread = None
            self.pipe.close()
            self.pipe = None

    def is_alive(self):
        """Is the ZAP thread currently running?"""
        if self.thread and self.thread.is_alive():
            return True
        return False

    def __del__(self):
        self.stop()

__all__ = ['ThreadAuthenticator']
