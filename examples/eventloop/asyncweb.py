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
from zmq.eventloop.future import Context as FutureContext

import tornado
from tornado import gen
from tornado import ioloop
from tornado import web


def slow_responder():
    """thread for slowly responding to replies."""
    ctx = zmq.Context()
    socket = ctx.socket(zmq.ROUTER)
    socket.linger = 0
    socket.bind('tcp://127.0.0.1:5555')
    i = 0
    while True:
        frame, msg = socket.recv_multipart()
        print("\nworker received %r\n" % msg, end='')
        time.sleep(random.randint(1,5))
        socket.send_multipart([frame, msg + b" to you too, #%i" % i])
        i += 1

def dot():
    """callback for showing that IOLoop is still responsive while we wait"""
    sys.stdout.write('.')
    sys.stdout.flush()

class TestHandler(web.RequestHandler):
    
    @gen.coroutine
    def get(self):
        ctx = FutureContext.instance()
        s = ctx.socket(zmq.DEALER)

        s.connect('tcp://127.0.0.1:5555')
        # send request to worker
        yield s.send(b'hello')

        # finish web request with worker's reply
        reply = yield s.recv_string()
        print("\nfinishing with %r\n" % reply)
        self.write(reply)

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
        print(' Interrupted')


if __name__ == "__main__":
    main()

