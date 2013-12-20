#!/usr/bin/env python

'''
Woodhouse extends Strawhouse with a name and password check.

This uses the PLAIN mechanism which does plain-text username and password
authentication). It's not really not secure, and anyone sniffing the
network (trivial with WiFi) can capture passwords and then login as if
they wanted.

Author: Chris Laws
'''

import zmq
import zmq.auth


def run():
    ''' Run woodhouse example '''

    valid_client_test_pass = False
    invalid_client_test_pass = False

    ctx = zmq.Context().instance()

    # Start an authenticator for this context.
    auth = zmq.auth.ThreadedAuthenticator(ctx)
    auth.start()
    auth.allow('127.0.0.1')
    # Instruct authenticator to handle PLAIN requests
    auth.configure_plain(domain='*', passwords={'admin': 'secret'})

    server = ctx.socket(zmq.PUSH)
    server.plain_server = True  # must come before bind
    server.bind('tcp://*:9000')

    client = ctx.socket(zmq.PULL)
    client.plain_username = 'admin'
    client.plain_password = 'secret'
    client.connect('tcp://127.0.0.1:9000')

    server.send("Hello")

    poller = zmq.Poller()
    poller.register(client, zmq.POLLIN)
    socks = dict(poller.poll(50))
    if client in socks and socks[client] == zmq.POLLIN:
        msg = client.recv()
        if msg == "Hello":
            valid_client_test_pass = True

    client.close()


    # now use invalid credentials - expect no msg received
    client2 = ctx.socket(zmq.PULL)
    client2.plain_username = 'admin'
    client2.plain_password = 'bogus'
    client2.connect('tcp://127.0.0.1:9000')

    server.send("World")

    poller = zmq.Poller()
    poller.register(client2, zmq.POLLIN)
    socks = dict(poller.poll(50))
    if client2 in socks and socks[client2] == zmq.POLLIN:
        msg = client.recv()
        if msg == "World":
            invalid_client_test_pass = False
    else:
        # no message is expected
        invalid_client_test_pass = True

    # stop auth thread
    auth.stop()

    if valid_client_test_pass and invalid_client_test_pass:
        print "Woodhouse test OK"
    else:
        print "Woodhouse test FAIL"


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