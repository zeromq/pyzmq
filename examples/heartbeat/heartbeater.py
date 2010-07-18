#!/usr/bin/env python
"""
A basic heartbeater using PUB and XREP sockets. pings are sent out on the PUB, and hearts
are tracked based on their XREQ identities.
For use with heart.py
"""

import time
import zmq
from zmq.eventloop import ioloop, zmqstream


class HeartBeater(object):
    """A basic HeartBeater class"""
    def __init__(self, loop, context,period=1000):
        self.loop = loop
        self.context = context
        self.period = period
        
        pub = context.socket(zmq.PUB)
        pub.bind('tcp://127.0.0.1:5555')
        xrep = context.socket(zmq.XREP)
        xrep.bind('tcp://127.0.0.1:5556')
        
        self.pingstream = zmqstream.ZMQStream(pub, self.loop)
        self.pongstream = zmqstream.ZMQStream(xrep, self.loop)
        self.pongstream.on_recv(self.handle_pong)
        
        self.hearts = set()
        self.responses = set()
        self.lifetime = 0
        self.tic = time.time()
        
        self.caller = ioloop.PeriodicCallback(self.reevaluate, period, self.loop)
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
        print "beating hearts: ",self.hearts
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
    ctx = zmq.Context()
    hb = HeartBeater(loop,ctx)
    
    loop.start()
