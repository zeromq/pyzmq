"""0MQ authentication related functions and classes."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


import datetime
import glob
import json
import logging
import os
from threading import Thread
import zmq
from zmq.utils import z85
from zmq.eventloop import ioloop, zmqstream


CURVE_ALLOW_ANY = '*'


_cert_secret_banner = """#   ****  Generated on {0} by pyzmq  ****
#   ZeroMQ CURVE **Secret** Certificate
#   DO NOT PROVIDE THIS FILE TO OTHER USERS nor change its permissions.

"""

_cert_public_banner = """#   ****  Generated on {0} by pyzmq  ****
#   ZeroMQ CURVE Public Certificate
#   Exchange securely, or use a secure mechanism to verify the contents
#   of this file after exchange. Store public certificates in your home
#   directory, in the .curve subdirectory.

"""

def _write_key_file(key_filename, banner, public_key, secret_key=None, metadata=None):
    """ Create a certificate file """
    with open(key_filename, 'w') as f:
        f.write(banner.format(datetime.datetime.now()))

        f.write('metadata\n')
        if metadata and isinstance(metadata, dict):
            for k, v in metadata.items():
                f.write("    {0} = {1}\n".format(k, v))

        f.write('curve\n')
        f.write("    public-key = \"{0}\"\n".format(public_key))

        if secret_key:
            f.write("    secret-key = \"{0}\"\n".format(secret_key))


def create_certificates(key_dir, name, metadata=None):
    '''
    Create zcert-esque public and private certificate files.
    Return the file paths to the public and secret certificate files.
    '''
    public_key, secret_key = zmq.curve_keypair()
    base_filename = os.path.join(key_dir, name)
    secret_key_file = "{0}.key_secret".format(base_filename)
    public_key_file = "{0}.key".format(base_filename)
    now = datetime.datetime.now()

    _write_key_file(public_key_file,
                    _cert_public_banner.format(now),
                    public_key)

    _write_key_file(secret_key_file,
                    _cert_secret_banner.format(now),
                    public_key,
                    secret_key=secret_key,
                    metadata=metadata)

    return public_key_file, secret_key_file


def load_certificate(filename):
    '''
    Load a certificate specified by filename and return the public
    and private keys read from the file. If the certificate file
    only contains the public key then secret_key will be None.
    '''
    public_key = None
    secret_key = None
    if not os.path.exists(filename):
        raise Exception("Invalid certificate file: {0}".format(filename))

    with open(filename, 'r') as f:
        lines = f.readlines()
        lines = filter(None, lines)
        lines = filter(lambda x: not x.startswith('#'), lines)
        lines = [x.strip() for x in lines]
        for line in lines:
            if line.startswith('public-key'):
                public_key = line.split(" = ")[1].strip().replace('"', '')
            if line.startswith('secret-key'):
                secret_key = line.split(" = ")[1].strip().replace('"', '')

    return public_key, secret_key


def load_certificates(location):
    ''' Load public keys from all certificates stored at location directory '''
    certs = {}
    if os.path.isdir(location):
        # Follow czmq pattern of public keys stored in *.key files.
        glob_string = os.path.join(location, "*.key")
        cert_files = glob.glob(glob_string)
        for cert_file in cert_files:
            try:
                public_key, _ = load_certificate(cert_file)
                if public_key:
                    certs[public_key] = 'OK'
            except Exception:
                logging.error("Certificate load error in {0}".format(cert_file))

    return certs


class Authenticator(object):
    '''
    An Authenticator object performs the ZAP authentication logic for all incoming
    connections in its context.

    Note:
    - libzmq provides four levels of security: default NULL (which zauth does
      not see), and authenticated NULL, PLAIN, and CURVE, which zauth can see.
    - until you add policies, all incoming NULL connections are allowed
    (classic ZeroMQ behavior), and all PLAIN and CURVE connections are denied.
    '''

    def __init__(self, context):
        if zmq.zmq_version_info() < (4,0):
            raise NotImplementedError("Security is only available in libzmq >= 4.0")
        self.context = context
        self.allow_any = False
        self.zap_socket = None
        self.whitelist = []
        self.blacklist = []
        # passwords is a dict keyed by domain and contains values
        # of dicts with username:password pairs.
        self.passwords = {}
        # certs is dict keyed by domain and contains values
        # of dicts keyed by the public keys from the specified location.
        self.certs = {}

    def start(self):
        ''' Start socket responsible for authenticating ZAP requests '''
        self.zap_socket = self.context.socket(zmq.REP)
        self.zap_socket.linger = 1
        self.zap_socket.bind("inproc://zeromq.zap.01")

    def stop(self):
        ''' Stop socket responsible for authenticating ZAP requests '''
        if self.zap_socket:
            self.zap_socket.close()
        self.zap_socket = None

    def allow(self, address):
        '''
        Allow (whitelist) a single IP address. For NULL, all clients from this
        address will be accepted. For PLAIN and CURVE, they will be allowed to
        continue with authentication. You can call this method multiple times
        to whitelist multiple IP addresses. If you whitelist a single address,
        any non-whitelisted addresses are treated as blacklisted.
        '''
        if address not in self.whitelist:
            self.whitelist.append(address)

    def deny(self, address):
        '''
        Deny (blacklist) a single IP address. For all security mechanisms, this
        rejects the connection without any further authentication. Use either a
        whitelist, or a blacklist, not not both. If you define both a whitelist
        and a blacklist, only the whitelist takes effect.
        '''
        if address not in self.blacklist:
            self.blacklist.append(address)

    def configure_plain(self, domain='*', passwords=None):
        '''
        Configure PLAIN authentication for a given domain. PLAIN authentication
        uses a plain-text password file. To cover all domains, use "*".
        You can modify the password file at any time; it is reloaded automatically.
        '''
        if passwords and isinstance(passwords, dict):
            self.passwords[domain] = passwords

    def configure_curve(self, domain='*', location=None):
        '''
        Configure CURVE authentication for a given domain. CURVE authentication
        uses a directory that holds all public client certificates, i.e. their
        public keys. The certificates must be in zcert_save () format.
        To cover all domains, use "*".
        You can add and remove certificates in that directory at any time.
        To allow all client keys without checking, specify CURVE_ALLOW_ANY for
        the location.
        '''
        # If location is CURVE_ALLOW_ANY then allow all clients. Otherwise
        # treat location as a directory that holds the certificates.
        if location == CURVE_ALLOW_ANY:
            self.allow_any = True
        else:
            self.allow_any = False
            if os.path.isdir(location):
                self.certs[domain] = load_certificates(location)
            else:
                logging.error("Invalid CURVE certs location: {0}".format(location))

    def handle_zap_message(self, msg):
        '''
        Perform ZAP authentication.
        '''
        version, sequence, domain, address, identity, mechanism = msg[:6]

        if (version != b"1.0"):
            self._send_zap_reply(sequence, b"400", b"Invalid version")
            return

        logging.debug("version: {0}, sequence: {1}, domain: {2}, " \
                      "address: {3}, identity: {4}, mechanism: {5}".format(version,
                        sequence, domain, address, identity, mechanism))


        # Is address is explicitly whitelisted or blacklisted?
        allowed = False
        denied = False
        reason = b"NO ACCESS"

        if self.whitelist:
            if address in self.whitelist:
                allowed = True
                logging.debug("PASSED (whitelist) address={0}".format(address))
            else:
                denied = True
                reason = b"Address not in whitelist"
                logging.debug("DENIED (not in whitelist) address={0}".format(address))

        elif self.blacklist:
            if address in self.blacklist:
                denied = True
                reason = b"Address is blacklisted"
                logging.debug("DENIED (blacklist) address={0}".format(address))
            else:
                allowed = True
                logging.debug("PASSED (not in blacklist) address={0}".format(address))

        # Perform authentication mechanism-specific checks if necessary
        if not denied:

            if mechanism == b'NULL' and not allowed:
                # For NULL, we allow if the address wasn't blacklisted
                logging.debug("ALLOWED (NULL)")
                allowed = True

            elif mechanism == b'PLAIN':
                # For PLAIN, even a whitelisted address must authenticate
                username, password = msg[6:]
                allowed, reason = self._authenticate_plain(domain, username, password)

            elif mechanism == b'CURVE':
                # For CURVE, even a whitelisted address must authenticate
                key = msg[6]
                allowed, reason = self._authenticate_curve(domain, key)

        if allowed:
            self._send_zap_reply(sequence, b"200", b"OK")
        else:
            self._send_zap_reply(sequence, b"400", reason)

    def _authenticate_plain(self, domain, username, password):
        '''
        Perform ZAP authentication check for PLAIN mechanism
        '''
        allowed = False
        reason = b""
        if self.passwords:
            # If no domain is not specified then use the default domain
            if not domain:
                domain = '*'

            if domain in self.passwords:
                if username in self.passwords[domain]:
                    if password == self.passwords[domain][username]:
                        allowed = True
                    else:
                        reason = b"Invalid password"
                else:
                    reason = b"Invalid username"
            else:
                reason = b"Invalid domain"

            if allowed:
                logging.debug("ALLOWED (PLAIN) domain={0} username={1} password={2}".format(domain,
                    username, password))
            else:
                logging.debug("DENIED {0}".format(reason))

        else:
            reason = b"No passwords defined"
            logging.debug("DENIED (PLAIN) {0}".format(reason))

        return allowed, reason

    def _authenticate_curve(self, domain, client_key):
        '''
        Perform ZAP authentication check for CURVE mechanism
        '''
        allowed = False
        reason = b""
        if self.allow_any:
            allowed = True
            reason = b"OK"
            logging.debug("ALLOWED (CURVE allow any client)")
        else:
            # If no explicit domain is specified then use the default domain
            if not domain:
                domain = '*'

            if domain in self.certs:
                # The certs dict stores keys in z85 format, convert binary key to z85 text
                z85_client_key = z85.encode(client_key)
                if z85_client_key in self.certs[domain]:
                    allowed = True
                    reason = b"OK"
                else:
                    reason = b"Unknown key"

                status = "DENIED"
                if allowed:
                    status = "ALLOWED"
                logging.debug("{0} (CURVE) domain={1} client_key={2}".format(status,
                    domain, z85_client_key))
            else:
                reason = b"Unknown domain"

        return allowed, reason

    def _send_zap_reply(self, sequence, status_code, status_text):
        '''
        Send a ZAP reply to the handler socket.
        '''
        uid = b"{0}".format(os.getuid()) if status_code == 'OK' else b""
        metadata = b""  # not currently used
        logging.debug("ZAP reply code={0} text={1}".format(status_code, status_text))
        reply = [b"1.0", sequence, status_code, status_text, uid, metadata]
        self.zap_socket.send_multipart(reply)


class AuthenticationThread(Thread):
    '''
    This class runs an Authenticator in a thread. This class is the
    background thread run by the ThreadedAuthenticator. Communication with
    the main thread is over the pipe.
    '''

    def __init__(self, context, endpoint):
        super(AuthenticationThread, self).__init__()
        self.context = context
        self.authenticator = Authenticator(context)

        # create a socket to communicate back to main thread.
        self.pipe = context.socket(zmq.PAIR)
        self.pipe.linger = 1
        self.pipe.connect(endpoint)

    def run(self):
        ''' Start the Authentication Agent thread task '''
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
        '''
        Handle a message from the ZAP socket.
        '''
        msg = self.authenticator.zap_socket.recv_multipart()
        if not msg: return
        self.authenticator.handle_zap_message(msg)

    def _handle_pipe(self):
        '''
        Handle a message from front-end API.
        '''
        terminate = False

        # Get the whole message off the pipe in one go
        msg = self.pipe.recv_multipart()

        if msg is None:
            terminate = True
            return terminate

        command = msg[0]
        logging.debug("auth received API command {0}".format(command))

        if command == 'ALLOW':
            address = msg[1]
            self.authenticator.allow(address)

        elif command == 'DENY':
            address = msg[1]
            self.authenticator.deny(address)

        elif command == 'PLAIN':
            domain = msg[1]
            json_passwords = msg[2]
            self.authenticator.configure_plain(domain, json.loads(json_passwords))

        elif command == 'CURVE':
            # For now we don't do anything with domains
            domain = msg[1]

            # If location is CURVE_ALLOW_ANY, allow all clients. Otherwise
            # treat location as a directory that holds the certificates.
            location = msg[2]
            self.authenticator.configure_curve(domain, location)

        elif command == 'TERMINATE':
            terminate = True

        else:
            logging.error("Invalid auth command from API: {0}".format(command))

        return terminate


class ThreadedAuthenticator(object):
    '''
    A security authenticator that performs authentication from a background thread

    All work is done by a background thread, the "agent", which we talk
    to over a pipe. This lets the agent do work asynchronously in the
    background while our application does other things. This is invisible to
    the caller, who sees a classic API.

    This design is modelled on czmq's zauth module.
    '''

    def __init__(self, context):
        self.context = context
        self.pipe = None
        self.pipe_endpoint = "inproc://{0}.inproc".format(id(self))
        self.thread = None

    def allow(self, address):
        '''
        Allow (whitelist) a single IP address. For NULL, all clients from this
        address will be accepted. For PLAIN and CURVE, they will be allowed to
        continue with authentication. You can call this method multiple times
        to whitelist multiple IP addresses. If you whitelist a single address,
        any non-whitelisted addresses are treated as blacklisted.
        '''
        self.pipe.send_multipart([b'ALLOW', address])

    def deny(self, address):
        '''
        Deny (blacklist) a single IP address. For all security mechanisms, this
        rejects the connection without any further authentication. Use either a
        whitelist, or a blacklist, not not both. If you define both a whitelist
        and a blacklist, only the whitelist takes effect.
        '''
        self.pipe.send_multipart([b'DENY', address])

    def configure_plain(self, domain='*', passwords=None):
        '''
        Configure PLAIN authentication for a given domain. PLAIN authentication
        uses a plain-text password file. To cover all domains, use "*".
        You can modify the password file at any time; it is reloaded automatically.
        '''
        if passwords:
            if isinstance(passwords, dict):
                passwords = json.dumps(passwords)
                self.pipe.send_multipart([b'PLAIN', domain, passwords])

    def configure_curve(self, domain='*', location=None):
        '''
        Configure CURVE authentication for a given domain. CURVE authentication
        uses a directory that holds all public client certificates, i.e. their
        public keys. The certificates must be in zcert_save () format.
        To cover all domains, use "*".
        You can add and remove certificates in that directory at any time.
        To allow all client keys without checking, specify CURVE_ALLOW_ANY for
        the location.
        '''
        self.pipe.send_multipart([b'CURVE', domain, location])

    def start(self):
        '''
        Start performing ZAP authentication
        '''
        # create a socket to communicate with auth thread.
        self.pipe = self.context.socket(zmq.PAIR)
        self.pipe.linger = 1
        self.pipe.bind(self.pipe_endpoint)
        self.thread = AuthenticationThread(self.context, self.pipe_endpoint)
        self.thread.start()

    def stop(self):
        '''
        Stop performing ZAP authentication
        '''
        if self.pipe:
            self.pipe.send(b'TERMINATE')
            if self.is_alive():
                self.thread.join()
            self.thread = None
            self.pipe.close()
            self.pipe = None

    def is_alive(self):
        ''' Is the Auth thread currently running ? '''
        if self.thread and self.thread.is_alive():
            return True
        return False

    def __del__(self):
        self.stop()


class IOLoopAuthenticator(Authenticator):
    ''' A security authenticator that is run in an event loop '''

    def __init__(self, context, io_loop=None):
        super(IOLoopAuthenticator, self).__init__(context)
        self.zapstream = None
        self.io_loop = io_loop or ioloop.IOLoop.current()

    def start(self, io_loop=None):
        ''' Run the ZAP authenticator in an event loop '''
        super(IOLoopAuthenticator, self).start()
        self.zapstream = zmqstream.ZMQStream(self.zap_socket, self.io_loop)
        self.zapstream.on_recv(self.handle_zap_message)

    def stop(self):
        ''' Stop performing ZAP authentication '''
        if self.zapstream:
            self.zapstream.on_recv(None)
            self.zapstream.close()
        self.zapstream = None
        super(IOLoopAuthenticator, self).stop()
