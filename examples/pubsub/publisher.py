"""A test that publishes NumPy arrays.

Currently the timing of this example is not accurate as it depends on the
subscriber and publisher being started at exactly the same moment. We should
use a REQ/REP side channel to synchronize the two processes at the beginning.
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

    print "Waiting for subscriber to connect..."
    # We need to sleep to allow the subscriber time to connect
    time.sleep(1.0)
    print "   Done."

    print "Sending arrays..."
    for i in range(array_count):
        a = numpy.random.rand(array_size, array_size)
        s.send_pyobj(a)
    print "   Done."
    print "Waiting for arrays to finish being sent..."

    time.sleep(1.0)
    print "   Done."

if __name__ == "__main__":
    main()
