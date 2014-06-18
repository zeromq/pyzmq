"""The display part of a simply two process chat app."""

# This file has been placed in the public domain.


import zmq
from zmq.utils.win32 import allow_interrupt


def main(addrs):
    context = zmq.Context()
    control = context.socket(zmq.PUB)
    control.bind('inproc://control')
    updates = context.socket(zmq.SUB)
    updates.setsockopt(zmq.SUBSCRIBE, "")
    updates.connect('inproc://control')
    for addr in addrs:
        print "Connecting to: ", addr
        updates.connect(addr)

    def interrupt_polling():
        """Fix CTRL-C on Windows using "self pipe trick"."""
        control.send_multipart(['', 'quit'])

    with allow_interrupt(interrupt_polling):
        message = ''
        while message != 'quit':
            message = updates.recv_multipart()
            if len(message) < 2:
                print 'Invalid message.'
                continue
            account = message[0]
            message = ' '.join(message[1:])
            if message == 'quit':
                print 'Killed by "%s".' % account
                break
            print '%s: %s' % (account, message)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print "usage: display.py <address> [,<address>...]"
        raise SystemExit
    main(sys.argv[1:])
