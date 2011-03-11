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


def main (argv):
    use_poll = '-p' in argv
    use_copy = '-c' in argv
    if use_copy:
        argv.remove('-c')
    if use_poll:
        argv.remove('-p')

    if len(argv) != 4:
        print ('usage: remote_lat [-c use-copy] [-p use-poll] <connect-to> <message-size> <roundtrip-count>')
        sys.exit(1)

    try:
        connect_to = argv[1]
        message_size = int(argv[2])
        roundtrip_count = int(argv[3])
    except (ValueError, OverflowError):
        print ('message-size and message-count must be integers')
        sys.exit(1)

    ctx = zmq.Context()
    s = ctx.socket(zmq.REQ)
    s.setsockopt(zmq.LINGER, -1)
    print (connect_to)
    s.connect(connect_to)
    if use_poll:
        p = zmq.Poller()
        p.register(s)

    # remove the b for Python2.5:
    msg = b' ' * message_size

    watch = zmq.Stopwatch()
    start = 0

    block = zmq.NOBLOCK if use_poll else 0
    
    watch.start()

    for i in range (0, roundtrip_count):
        if use_poll:
            res = p.poll()
            assert(res[0][1] & zmq.POLLOUT)
        s.send(msg, block, copy=use_copy)

        if use_poll:
            res = p.poll()
            assert(res[0][1] & zmq.POLLIN)
        msg = s.recv(block, copy=use_copy)
        
        assert len (msg) == message_size

    elapsed = watch.stop()

    # remove the b for Python2.5:
    t = s.send(b'done', copy=False, track=True)
    t.wait()

    latency = elapsed / (roundtrip_count * 2)

    print ("message size: %i [B]" % (message_size, ))
    print ("roundtrip count: %i" % (roundtrip_count, ))
    print ("mean latency: %.3f [us]" % (latency, ))

    s.close()
    ctx.term()
    return latency

if __name__ == "__main__":
    main (sys.argv)


