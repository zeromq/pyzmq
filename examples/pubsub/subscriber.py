import sys
import time

import zmq
import numpy

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

    ctx = zmq.Context(1,1)
    s = ctx.create_socket(zmq.SUB)
    print "Connecting..."
    s.connect(connect_to)
    print "   Done."
    s.setsockopt(zmq.SUBSCRIBE,'')

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
