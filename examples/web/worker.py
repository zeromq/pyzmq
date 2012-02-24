"""The master web server."""

import logging
logging.basicConfig(level=logging.DEBUG)
import time
from zmq.eventloop import ioloop
ioloop.install()
from tornado import web

from zmq.web import ZMQApplication

class FooHandler(web.RequestHandler):

    def get(self):
        self.finish('bar')

class SleepHandler(web.RequestHandler):

    def get(self):
        t = float(self.get_argument('t',1.0))
        time.sleep(t)
        self.finish({'status':'awake','t':t})

application = ZMQApplication(
    [
        (r"/foo", FooHandler),
        (r"/foo/sleep", SleepHandler)
    ],
)

application.connect('tcp://127.0.0.1:5555')
ioloop.IOLoop.instance().start()
