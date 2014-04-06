"""A test that subscribes to NumPy arrays.

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

def sync(connect_to):
    # use connect socket + 1
    sync_with = ':'.join(connect_to.split(':')[:-1] +
                         [str(int(connect_to.split(':')[-1]) + 1)]
                        )
    ctx = zmq.Context.instance()
    s = ctx.socket(zmq.REQ)
    s.connect(sync_with)
    s.send('READY')
    s.recv()

def main():
    if len (sys.argv) != 3:
        print 'usage: subscriber <connect_to> <array-count>'
        sys.exit (1)

    try:
        connect_to = sys.argv[1]
        array_count = int (sys.argv[2])
    except (ValueError, OverflowError), e:
        print 'array-count must be integers'
        sys.exit (1)

    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.connect(connect_to)
    s.setsockopt(zmq.SUBSCRIBE,'')

    sync(connect_to)

    start = time.clock()

    print "Receiving arrays..."
    for i in range(array_count):
        a = s.recv_pyobj()
    print "   Done."

    end = time.clock()

    elapsed = (end - start) * 1000000
    if elapsed == 0:
    	elapsed = 1
    throughput = (1000000.0 * float (array_count)) / float (elapsed)
    message_size = a.nbytes
    megabits = float (throughput * message_size * 8) / 1000000

    print "message size: %.0f [B]" % (message_size, )
    print "array count: %.0f" % (array_count, )
    print "mean throughput: %.0f [msg/s]" % (throughput, )
    print "mean throughput: %.3f [Mb/s]" % (megabits, )

    time.sleep(1.0)

if __name__ == "__main__":
    main()
