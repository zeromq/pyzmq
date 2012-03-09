#!/usr/bin/env python
"""Simple example of publish/subscribe illustrating topics.

Publisher and subscriber can be started in any order, though if publisher
starts first, any messages sent before subscriber starts are lost.  More than
one subscriber can listen, and they can listen to  different topics.

Topic filtering is done simply on the start of the string, e.g. listening to
's' will catch 'sports...' and 'stocks'  while listening to 'w' is enough to
catch 'weather'.
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger, Fernando Perez
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys
import time

import zmq
import numpy

def main():
    if len (sys.argv) < 2:
        print 'usage: subscriber <connect_to> [topic topic ...]'
        sys.exit (1)

    connect_to = sys.argv[1]
    topics = sys.argv[2:]

    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.connect(connect_to)

    # manage subscriptions
    if not topics:
        print "Receiving messages on ALL topics..."
        s.setsockopt(zmq.SUBSCRIBE,'')
    else:
        print "Receiving messages on topics: %s ..." % topics
        for t in topics:
            s.setsockopt(zmq.SUBSCRIBE,t)
    print
    try:
        while True:
            topic, msg = s.recv_multipart()
            print '   Topic: %s, msg:%s' % (topic, msg)
    except KeyboardInterrupt:
        pass
    print "Done."

if __name__ == "__main__":
    main()
