"""A frontend web server with load balanced request handlers.

This example shows how to use zmq.web to run a Tornado web server with 
individual request handlers in separate backend processes. This file implements
the frontend logic and needs to be run with 1 or more instances of backend.py.

To run this example:

* Start one instance of frontend.py.
* Start one or more instances of backend.py.
* Hit the URLs http://127.0.0.1/foo and http://127.0.0.1/foo/sleep?t=1. The
  t parameter of this last URL can be changed to something greater than 2 to
  observe the timeout behavior.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2012 Brian Granger, Min Ragan-Kelley
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

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
    # We use a timeout of 2000ms, after which a status of 504 is returned.
    # All URLs beginning with /foo will be handled by the backend.
    [(r"/foo\S*", ZMQRequestHandlerProxy, {'proxy':proxy,'timeout':2000})]
)

logging.info("Starting frontend HTTP server")
application.listen(8888)
ioloop.IOLoop.instance().start()
