"""The display part of a simply two process chat app."""

# This file has been placed in the public domain.
from typing import List

import zmq
from zmq.utils.win32 import allow_interrupt


def main(addrs: List[str]):
    context = zmq.Context()
    control = context.socket(zmq.PUB)
    control.bind('inproc://control')
    updates = context.socket(zmq.SUB)
    updates.setsockopt(zmq.SUBSCRIBE, "")
    updates.connect('inproc://control')
    for addr in addrs:
        print("Connecting to: ", addr)
        updates.connect(addr)

    def interrupt_polling():
        """Fix CTRL-C on Windows using "self pipe trick"."""
        control.send_multipart(['', 'quit'])

    with allow_interrupt(interrupt_polling):
        message = ''
        while message != 'quit':
            recvd = updates.recv_multipart()
            if len(recvd) < 2:
                print('Invalid message.')
                continue
            account = recvd[0].decode("utf8")
            message = ' '.join(b.decode("utf8") for b in recvd[1:])
            if message == 'quit':
                print(f'Killed by {account}.')
                break
            print(f'{account}: {message}')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("usage: display.py <address> [,<address>...]")
        raise SystemExit
    main(sys.argv[1:])
