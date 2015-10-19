"""Async web request example with tornado.

Requests to localhost:8888 will be relayed via 0MQ to a slow responder,
who will take 1-5 seconds to respond.  The tornado app will remain responsive
duriung this time, and when the worker replies, the web request will finish.

A '.' is printed every 100ms to demonstrate that the zmq request is not blocking
the event loop.
"""


import sys
import random
import threading
import time

import zmq
from zmq.eventloop import ioloop, zmqstream

"""
ioloop.install() must be called prior to instantiating *any* tornado objects,
and ideally before importing anything from tornado, just to be safe.

install() sets the singleton instance of tornado.ioloop.IOLoop with zmq's
IOLoop. If this is not done properly, multiple IOLoop instances may be
created, which will have the effect of some subset of handlers never being
called, because only one loop will be running.
"""

ioloop.install()

import tornado
from tornado import web


def slow_responder():
    """thread for slowly responding to replies."""
    ctx = zmq.Context.instance()
    socket = ctx.socket(zmq.REP)
    socket.linger = 0
    socket.bind('tcp://127.0.0.1:5555')
    i=0
    while True:
        msg = socket.recv()
        print "\nworker received %r\n" % msg
        time.sleep(random.randint(1,5))
        socket.send(msg + " to you too, #%i" % i)
        i+=1

def dot():
    """callback for showing that IOLoop is still responsive while we wait"""
    sys.stdout.write('.')
    sys.stdout.flush()

class TestHandler(web.RequestHandler):
    
    @web.asynchronous
    def get(self):
        ctx = zmq.Context.instance()
        s = ctx.socket(zmq.REQ)
        s.connect('tcp://127.0.0.1:5555')
        # send request to worker
        s.send('hello')
        self.stream = zmqstream.ZMQStream(s)
        self.stream.on_recv(self.handle_reply)
    
    def handle_reply(self, msg):
        # finish web request with worker's reply
        reply = msg[0]
        print "\nfinishing with %r\n" % reply,
        self.stream.close()
        self.write(reply)
        self.finish()

def main():
    worker = threading.Thread(target=slow_responder)
    worker.daemon=True
    worker.start()
    
    application = web.Application([(r"/", TestHandler)])
    beat = ioloop.PeriodicCallback(dot, 100)
    beat.start()
    application.listen(8888)
    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print ' Interrupted'
    
    
if __name__ == "__main__":
    main()

