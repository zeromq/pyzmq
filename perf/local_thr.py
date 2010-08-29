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

import sys
import time
import zmq

def main ():
    use_poll = '-p' in sys.argv
    use_copy = '-c' in sys.argv
    if use_copy:
        sys.argv.remove('-c')
    if use_poll:
        sys.argv.remove('-p')

    if len (sys.argv) != 4:
        print 'usage: local_thr [-c use-copy] [-p use-poll] <bind-to> <message-size> <message-count>'
        sys.exit(1)

    try:
        bind_to = sys.argv[1]
        message_size = int(sys.argv[2])
        message_count = int(sys.argv[3])
    except (ValueError, OverflowError), e:
        print 'message-size and message-count must be integers'
        sys.exit(1)

    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)

    #  Add your socket options here.
    #  For example ZMQ_RATE, ZMQ_RECOVERY_IVL and ZMQ_MCAST_LOOP for PGM.
    s.setsockopt(zmq.SUBSCRIBE , "");

    if use_poll:
        p = zmq.Poller()
        p.register(s)

    s.bind(bind_to)

    # Wait for the other side to connect.
    time.sleep(2.0)

    msg = s.recv()
    assert len (msg) == message_size

    clock = zmq.Stopwatch()
    start = 0
    clock.start()
    # start = time.clock()

    for i in range (1, message_count):
        if use_poll:
            res = p.poll()
            assert(res[0][1] & zmq.POLLIN)
        msg = s.recv(zmq.NOBLOCK if use_poll else 0, copy=use_copy)
        assert len(msg) == message_size

        end = clock.stop()
        # end = time.clock()

    elapsed = (end - start)
    # elapsed = (end - start) * 1000000 # use with time.clock
    if elapsed == 0:
    	elapsed = 1
    throughput = (1000000.0 * float(message_count)) / float(elapsed)
    megabits = float(throughput * message_size * 8) / 1000000

    print "message size: %.0f [B]" % (message_size, )
    print "message count: %.0f" % (message_count, )
    print "mean throughput: %.0f [msg/s]" % (throughput, )
    print "mean throughput: %.3f [Mb/s]" % (megabits, )

    # Let the context finish messaging before ending.
    # You may need to increase this time for longer or many messages.
    time.sleep(2.0)

if __name__ == "__main__":
    main ()

