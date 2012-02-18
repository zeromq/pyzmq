"""The master web server."""

from zmq.eventloop import ioloop
ioloop.install()
from tornado import web

from zmq.web.zmqweb import ZMQWebApplication, ZMQRequestHandler

class FooHandler(ZMQRequestHandler):

    def get(self):
        self.finish('bar')

application = ZMQWebApplication(
    [(r"/foo", FooHandler)]
)

application.connect('tcp://127.0.0.1:5555')
ioloop.IOLoop.instance().start()
