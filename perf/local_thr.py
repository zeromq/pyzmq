#
#    Copyright (c) 2007-2010 iMatix Corporation
#
#    This file is part of 0MQ.
#
#    0MQ is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    0MQ is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import time
import zmq


def main (argv):
    use_poll = '-p' in argv
    use_copy = '-c' in argv
    if use_copy:
        argv.remove('-c')
    if use_poll:
        argv.remove('-p')

    if len (argv) != 4:
        print ('usage: local_thr [-c use-copy] [-p use-poll] <bind-to> <message-size> <message-count>')
        sys.exit(1)

    try:
        bind_to = argv[1]
        message_size = int(argv[2])
        message_count = int(argv[3])
    except (ValueError, OverflowError):
        print ('message-size and message-count must be integers')
        sys.exit(1)

    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)

    #  Add your socket options here.
    #  For example ZMQ_RATE, ZMQ_RECOVERY_IVL and ZMQ_MCAST_LOOP for PGM.
    # remove the b for Python2.5:
    s.setsockopt(zmq.SUBSCRIBE , b'')

    if use_poll:
        p = zmq.Poller()
        p.register(s)

    s.bind(bind_to)

    watch = zmq.Stopwatch()
    block = zmq.NOBLOCK if use_poll else 0
    
    # Wait for the other side to connect.
    msg = s.recv()
    assert len (msg) == message_size
    
    watch.start()
    for i in range (message_count-1):
        if use_poll:
            res = p.poll()
            assert(res[0][1] & zmq.POLLIN)
        msg = s.recv(block, copy=use_copy)
    elapsed = watch.stop()

    if elapsed == 0:
        elapsed = 1
    
    throughput = (1e6 * float(message_count)) / float(elapsed)
    megabits = float(throughput * message_size * 8) / 1e6

    print ("message size: %i [B]" % (message_size, ))
    print ("message count: %i" % (message_count, ))
    print ("mean throughput: %.0f [msg/s]" % (throughput, ))
    print ("mean throughput: %.3f [Mb/s]" % (megabits, ))

    s.close()
    ctx.term()
    return throughput

if __name__ == "__main__":
    main (sys.argv)

