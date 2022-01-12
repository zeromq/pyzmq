#!/usr/bin/env python
"""

For use with heart.py

A basic heartbeater using PUB and ROUTER sockets. pings are sent out on the PUB, and hearts
are tracked based on their DEALER identities.

You can start many hearts with heart.py, and the heartbeater will monitor all of them, and notice when they stop responding.

Authors
-------
* MinRK
"""

import time
from typing import Set

from tornado import ioloop

import zmq
from zmq.eventloop import zmqstream


class HeartBeater:
    """A basic HeartBeater class
    pingstream: a PUB stream
    pongstream: an ROUTER stream"""

    def __init__(
        self,
        loop: ioloop.IOLoop,
        pingstream: zmqstream.ZMQStream,
        pongstream: zmqstream.ZMQStream,
        period: int = 1000,
    ):
        self.loop = loop
        self.period = period

        self.pingstream = pingstream
        self.pongstream = pongstream
        self.pongstream.on_recv(self.handle_pong)

        self.hearts: Set = set()
        self.responses: Set = set()
        self.lifetime = 0
        self.tic = time.monotonic()

        self.caller = ioloop.PeriodicCallback(self.beat, period)
        self.caller.start()

    def beat(self):
        toc = time.monotonic()
        self.lifetime += toc - self.tic
        self.tic = toc
        print(self.lifetime)
        # self.message = str(self.lifetime)
        goodhearts = self.hearts.intersection(self.responses)
        heartfailures = self.hearts.difference(goodhearts)
        newhearts = self.responses.difference(goodhearts)
        # print(newhearts, goodhearts, heartfailures)
        for heart in newhearts:
            self.handle_new_heart(heart)
        for heart in heartfailures:
            self.handle_heart_failure(heart)
        self.responses = set()
        print(f"{len(self.hearts)} beating hearts: {self.hearts}")
        self.pingstream.send(str(self.lifetime))

    def handle_new_heart(self, heart):
        print(f"yay, got new heart {heart}!")
        self.hearts.add(heart)

    def handle_heart_failure(self, heart):
        print(f"Heart {heart} failed :(")
        self.hearts.remove(heart)

    def handle_pong(self, msg):
        "if heart is beating"
        if msg[1] == str(self.lifetime):
            self.responses.add(msg[0])
        else:
            print("got bad heartbeat (possibly old?): %s" % msg[1])


# sub.setsockopt(zmq.SUBSCRIBE)


if __name__ == '__main__':
    loop = ioloop.IOLoop()
    context = zmq.Context()
    pub = context.socket(zmq.PUB)
    pub.bind('tcp://127.0.0.1:5555')
    router = context.socket(zmq.ROUTER)
    router.bind('tcp://127.0.0.1:5556')

    outstream = zmqstream.ZMQStream(pub, loop)
    instream = zmqstream.ZMQStream(router, loop)

    hb = HeartBeater(loop, outstream, instream)

    loop.start()
