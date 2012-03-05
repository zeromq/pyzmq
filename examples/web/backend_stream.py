"""A backend request handler process.

This file uses zmq.web to implement the backend logic for load balanced
Tornado request handlers.

This version uses a streaming message protocol to enable the backend to send
the HTTP body back to the frontend/browser in multiple asynchronous chunks.
To enable streaming mode, you have to use ZMQStreamingApplicationProxy in
the frontend and ZMQStreamingHTTPRequest in the backend.

To run this example:

* Start one instance of frontend_stream.py.
* Start one or more instances of backend_stream.py.
* Hit the URLs http://127.0.0.1/foo and http://127.0.0.1/foo/sleep?t=1. The
  t parameter of this last URL can be changed to something greater than 10 to
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

from zmq.web import ZMQApplication, ZMQStreamingHTTPRequest

def flush_callback():
    logging.info('Done flushing zmq buffers')

class FooHandler(web.RequestHandler):

    @web.asynchronous
    def get(self):
        self.set_header('Handler', 'FooHandler')
        # Each write/flush pair is send back to the frontend/browser immediately.
        self.write('pow\n')
        self.flush(callback=flush_callback)
        self.bam_count = 10
        def bam_and_finish():
            if self.bam_count>0:
                # Each write/flush pair is send back to the frontend/browser immediately.
                self.write('bam\n')
                self.flush(callback=flush_callback)
                self.bam_count -= 1
            else:
                self.bam_pc.stop()
                # Calling finish sends a final message to finish the request.
                self.finish()
        self.bam_pc = ioloop.PeriodicCallback(bam_and_finish, 1000, ioloop.IOLoop.instance())
        self.bam_pc.start()

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
    # To use streaming replies, we set need to http_request_class to
    # ZMQStreamingHTTPRequest. The frontend needs to use
    # ZMQStreamingApplicationProxy in this case.
    http_request_class=ZMQStreamingHTTPRequest
)

application.connect('tcp://127.0.0.1:5555')
ioloop.IOLoop.instance().start()
