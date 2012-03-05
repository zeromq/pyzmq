"""A backend request handler process.

This file uses zmq.web to implement the backend logic for load balanced
Tornado request handlers.

To run this example:

* Start one instance of frontend.py.
* Start one or more instances of backend.py.
* Hit the URLs http://127.0.0.1/foo and http://127.0.0.1/foo/sleep?t=1. The
  t parameter of this last URL can be changed to something greater than 2 to
  observe the timeout behavior.
 
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2012 Brian Granger, Min Ragan-Kelley
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import logging
logging.basicConfig(level=logging.DEBUG)
import time

from zmq.eventloop import ioloop
ioloop.install()
from tornado import web

from zmq.web import ZMQApplication

class FooHandler(web.RequestHandler):

    def get(self):
        self.set_header('Handler', 'FooHandler')
        self.finish('bar')

class SleepHandler(web.RequestHandler):

    def get(self):
        t = float(self.get_argument('t',1.0))
        time.sleep(t)
        self.finish({'status':'awake','t':t})

application = ZMQApplication(
    [
        #  A single ZMQApplication can run multiple request handlers, but the
        # frontend must use a URL regular expression that matches all of the
        # patterns in the backend.
        (r"/foo", FooHandler),
        (r"/foo/sleep", SleepHandler)
    ],
)

application.connect('tcp://127.0.0.1:5555')
ioloop.IOLoop.instance().start()
