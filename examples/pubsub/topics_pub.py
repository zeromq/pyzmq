#!/usr/bin/env python
"""Simple example of publish/subscribe illustrating topics.

Publisher and subscriber can be started in any order, though if publisher
starts first, any messages sent before subscriber starts are lost.  More than
one subscriber can listen, and they can listen to  different topics.

Topic filtering is done simply on the start of the string, e.g. listening to
's' will catch 'sports...' and 'stocks'  while listening to 'w' is enough to
catch 'weather'.
"""

# -----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file LICENSE.BSD, distributed as part of this software.
# -----------------------------------------------------------------------------

import itertools
import sys
import time

import zmq


def main() -> None:
    if len(sys.argv) != 2:
        print('usage: publisher <bind-to>')
        sys.exit(1)

    bind_to = sys.argv[1]

    all_topics = [
        b'sports.general',
        b'sports.football',
        b'sports.basketball',
        b'stocks.general',
        b'stocks.GOOG',
        b'stocks.AAPL',
        b'weather',
    ]

    ctx = zmq.Context()
    s = ctx.socket(zmq.PUB)
    s.bind(bind_to)

    print("Starting broadcast on topics:")
    print(f"   {all_topics}")
    print("Hit Ctrl-C to stop broadcasting.")
    print("Waiting so subscriber sockets can connect...")
    print("")
    time.sleep(1.0)

    msg_counter = itertools.count()
    try:
        for topic in itertools.cycle(all_topics):
            msg_body = str(next(msg_counter))
            print(f"   Topic: {topic.decode('utf8')}, msg:{msg_body}")
            s.send_multipart([topic, msg_body.encode("utf8")])
            # short wait so we don't hog the cpu
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    print("Waiting for message queues to flush...")
    time.sleep(0.5)
    print("Done.")


if __name__ == "__main__":
    main()
