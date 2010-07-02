#!/usr/bin/env python
"""Simple example of publish/subscribe illustrating topics.

Publisher and subscriber can be started in any order, though if publisher
starts first, any messages sent before subscriber starts are lost.  More than
one subscriber can listen, and they can listen to  different topics.

Topic filtering is done simply on the start of the string, e.g. listening to
's' will catch 'sports...' and 'stocks'  while listening to 'w' is enough to
catch 'weather'.
"""

#
#    Copyright (c) 2010 Brian E. Granger, Fernando Perez
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import itertools
import sys
import time

import zmq

def main():
    if len (sys.argv) != 2:
        print 'usage: publisher <bind-to>'
        sys.exit (1)

    bind_to = sys.argv[1]

    all_topics = ['sports.general','sports.football','sports.basketball',
                  'stocks.general','stocks.GOOG','stocks.AAPL',
                  'weather']

    ctx = zmq.Context()
    s = ctx.socket(zmq.PUB)
    s.bind(bind_to)

    print "Starting broadcast on topics:"
    print "   %s" % all_topics
    print "Hit Ctrl-C to stop broadcasting."
    print "Waiting so subscriber sockets can connect..."
    print
    time.sleep(1.0)

    msg_counter = itertools.count()
    try:
        for topic in itertools.cycle(all_topics):
            msg_body = str(msg_counter.next())
            print '   Topic: %s, msg:%s' % (topic, msg_body)
            s.send_multipart([topic, msg_body])
            # short wait so we don't hog the cpu
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    print "Waiting for message queues to flush..."
    time.sleep(0.5)
    print "Done."

if __name__ == "__main__":
    main()
