"""The master web server."""

from zmq.eventloop import ioloop
ioloop.install()
from tornado import web

from zmq.web.zmqweb import ZMQWebApplicationProxy, ZMQRequestHandlerProxy

proxy = ZMQWebApplicationProxy()
proxy.bind('tcp://127.0.0.1:5555')

application = web.Application(
    [(r"/foo", ZMQRequestHandlerProxy, {'proxy':proxy})]
)

application.listen(8888)
ioloop.IOLoop.instance().start()
