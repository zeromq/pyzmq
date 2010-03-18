"""
* A kernel/engine subscribes to a set of queues.
* The engine has a scheduler that determines which queues it consumes from
and how.

Types of queues:

- All engines same.
- Just one engine or a subset.
- Dynamic load balanced.

Are the queues in a graph with only one exposed to the engine, or does
the engine get to work directly with the different queue types.

Different queue types may have different symantics - like error handling.

"""

import sys
import time

import zmq

def main():
    ctx = zmq.Context()
    s = ctx.socket(zmq.REP)
    s.bind('tcp://127.0.0.1:5555')

    time.sleep(5)
    for i in range(20):
        print "Receiving request..."
        msg = s.recv()
        print "Got request: ", msg
        print "Replying..."
        s.send('message%i' % i)

if __name__ == '__main__':
    main()
