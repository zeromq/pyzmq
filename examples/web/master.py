"""The master web server."""

import logging
logging.basicConfig(level=logging.DEBUG)

from zmq.eventloop import ioloop
ioloop.install()
from tornado import web

from zmq.web import (
    ZMQApplicationProxy, ZMQRequestHandlerProxy
)

proxy = ZMQApplicationProxy()
proxy.bind('tcp://127.0.0.1:5555')

application = web.Application(
    [(r"/foo\S*", ZMQRequestHandlerProxy, {'proxy':proxy,'timeout':2000})]
)

logging.info("Starting master HTTP server")
application.listen(8888)
ioloop.IOLoop.instance().start()
