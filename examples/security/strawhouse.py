#!/usr/bin/env python

'''
Allow or deny clients based on IP address.

Strawhouse, which is plain text with filtering on IP addresses. It still
uses the NULL mechanism, but we install an authentication hook that checks
the IP address against a whitelist or blacklist and allows or denies it
accordingly.

Author: Chris Laws
'''

import zmq
import zmq.auth


def run(verbose=False):
    ''' Run stawhouse client '''

    allow_test_pass = False
    deny_test_pass = False

    ctx = zmq.Context().instance()

    # Start an authenticator for this context.
    auth = zmq.auth.ThreadedAuthenticator(ctx)
    auth.start()

    # Part 1 - demonstrate allowing clients based on IP address
    auth.allow('127.0.0.1')

    server = ctx.socket(zmq.PUSH)
    server.zap_domain = 'global'  # must come before bind
    server.bind('tcp://*:9000')

    client_allow = ctx.socket(zmq.PULL)
    client_allow.connect('tcp://127.0.0.1:9000')

    server.send("Hello")

    msg = client_allow.recv()
    if msg == "Hello":
        allow_test_pass = True
    else:
        allow_test_pass = False

    client_allow.close()

    # Part 2 - demonstrate denying clients based on IP address
    auth.deny('127.0.0.1')

    server.send("Hello")

    client_deny = ctx.socket(zmq.PULL)
    client_deny.connect('tcp://127.0.0.1:9000')

    poller = zmq.Poller()
    poller.register(client_deny, zmq.POLLIN)
    socks = dict(poller.poll(50))
    if client_deny in socks and socks[client_deny] == zmq.POLLIN:
        msg = client_deny.recv()
        if msg == "Hello":
            deny_test_pass = False
    else:
        deny_test_pass = True

    client_deny.close()

    auth.stop()  # stop auth thread

    if allow_test_pass and deny_test_pass:
        print "Strawhouse test OK"
    else:
        print "Strawhouse test FAIL"


if __name__ == '__main__':
    import logging
    import sys

    if zmq.zmq_version_info() < (4,0):
        raise RuntimeError("Security is not supported in libzmq version < 4.0. libzmq version {0}".format(zmq.zmq_version()))

    verbose = False
    if '-v' in sys.argv:
        verbose = True

    if verbose:
        logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s',
                            level=logging.DEBUG)

    run()