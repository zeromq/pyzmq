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
import zmq
from zmq.eventloop import ioloop, zmqstream


class HeartBeater(object):
    """A basic HeartBeater class
    pingstream: a PUB stream
    pongstream: an ROUTER stream"""
    
    def __init__(self, loop, pingstream, pongstream, period=1000):
        self.loop = loop
        self.period = period
        
        self.pingstream = pingstream
        self.pongstream = pongstream
        self.pongstream.on_recv(self.handle_pong)
        
        self.hearts = set()
        self.responses = set()
        self.lifetime = 0
        self.tic = time.time()
        
        self.caller = ioloop.PeriodicCallback(self.beat, period, self.loop)
        self.caller.start()
    
    def beat(self):
        toc = time.time()
        self.lifetime += toc-self.tic
        self.tic = toc
        print self.lifetime
        # self.message = str(self.lifetime)
        goodhearts = self.hearts.intersection(self.responses)
        heartfailures = self.hearts.difference(goodhearts)
        newhearts = self.responses.difference(goodhearts)
        # print newhearts, goodhearts, heartfailures
        map(self.handle_new_heart, newhearts)
        map(self.handle_heart_failure, heartfailures)
        self.responses = set()
        print "%i beating hearts: %s"%(len(self.hearts),self.hearts)
        self.pingstream.send(str(self.lifetime))
    
    def handle_new_heart(self, heart):
        print "yay, got new heart %s!"%heart
        self.hearts.add(heart)
    
    def handle_heart_failure(self, heart):
        print "Heart %s failed :("%heart
        self.hearts.remove(heart)
        
    
    def handle_pong(self, msg):
        "if heart is beating"
        if msg[1] == str(self.lifetime):
            self.responses.add(msg[0])
        else:
            print "got bad heartbeat (possibly old?): %s"%msg[1]
        
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
