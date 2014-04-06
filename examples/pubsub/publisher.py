"""A test that publishes NumPy arrays.

Uses REQ/REP (on PUB/SUB socket + 1) to synchronize
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys
import time

import zmq
import numpy

def sync(bind_to):
    # use bind socket + 1
    sync_with = ':'.join(bind_to.split(':')[:-1] +
                         [str(int(bind_to.split(':')[-1]) + 1)])
    ctx = zmq.Context.instance()
    s = ctx.socket(zmq.REP)
    s.bind(sync_with)
    print "Waiting for subscriber to connect..."
    s.recv()
    print "   Done."
    s.send('GO')

def main():
    if len (sys.argv) != 4:
        print 'usage: publisher <bind-to> <array-size> <array-count>'
        sys.exit (1)

    try:
        bind_to = sys.argv[1]
        array_size = int(sys.argv[2])
        array_count = int (sys.argv[3])
    except (ValueError, OverflowError), e:
        print 'array-size and array-count must be integers'
        sys.exit (1)

    ctx = zmq.Context()
    s = ctx.socket(zmq.PUB)
    s.bind(bind_to)

    sync(bind_to)

    print "Sending arrays..."
    for i in range(array_count):
        a = numpy.random.rand(array_size, array_size)
        s.send_pyobj(a)
    print "   Done."

if __name__ == "__main__":
    main()
