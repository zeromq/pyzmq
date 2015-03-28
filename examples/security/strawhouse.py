#!/usr/bin/env python

'''
Allow or deny clients based on IP address.

Strawhouse, which is plain text with filtering on IP addresses. It still
uses the NULL mechanism, but we install an authentication hook that checks
the IP address against a whitelist or blacklist and allows or denies it
accordingly.

Author: Chris Laws
'''

import logging
import sys

import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator


def run():
    '''Run strawhouse client'''

    allow_test_pass = False
    deny_test_pass = False

    ctx = zmq.Context.instance()

    # Start an authenticator for this context.
    auth = ThreadAuthenticator(ctx)
    auth.start()

    # Part 1 - demonstrate allowing clients based on IP address
    auth.allow('127.0.0.1')

    server = ctx.socket(zmq.PUSH)
    server.zap_domain = b'global'  # must come before bind
    server.bind('tcp://*:9000')

    client_allow = ctx.socket(zmq.PULL)
    client_allow.connect('tcp://127.0.0.1:9000')

    server.send(b"Hello")

    msg = client_allow.recv()
    if msg == b"Hello":
        allow_test_pass = True

    client_allow.close()

    # Part 2 - demonstrate denying clients based on IP address
    auth.stop()
    
    auth = ThreadAuthenticator(ctx)
    auth.start()
    
    auth.deny('127.0.0.1')

    client_deny = ctx.socket(zmq.PULL)
    client_deny.connect('tcp://127.0.0.1:9000')
    
    if server.poll(50, zmq.POLLOUT):
        server.send(b"Hello")

        if client_deny.poll(50):
            msg = client_deny.recv()
        else:
            deny_test_pass = True
    else:
        deny_test_pass = True

    client_deny.close()

    auth.stop()  # stop auth thread

    if allow_test_pass and deny_test_pass:
        logging.info("Strawhouse test OK")
    else:
        logging.error("Strawhouse test FAIL")


if __name__ == '__main__':
    if zmq.zmq_version_info() < (4,0):
        raise RuntimeError("Security is not supported in libzmq version < 4.0. libzmq version {0}".format(zmq.zmq_version()))

    if '-v' in sys.argv:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")

    run()
