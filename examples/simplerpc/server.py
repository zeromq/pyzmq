"""A simple RPC server that show how to run multiple RPC services."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012. Brian Granger, Min Ragan-Kelley  
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------


import time

from zmq.rpc.simplerpc import RPCService, rpc_method, JSONSerializer
from zmq.eventloop import ioloop
from zmq.utils import jsonapi


class Echo(RPCService):

    @rpc_method
    def echo(self, s):
        print "%r echo %r" % (self.urls, s)
        return s

    @rpc_method
    def sleep(self, t):
        time.sleep(t)

    @rpc_method
    def error(self):
        raise ValueError('raising ValueError for fun!')

class Math(RPCService):

    @rpc_method
    def add(self, a, b):
        print "%r add %r %r" % (self.urls, a, b)
        return a+b

    @rpc_method
    def subtract(self, a, b):
        print "%r subtract %r %r" % (self.urls, a, b)
        return a-b

    @rpc_method
    def multiply(self, a, b):
        print "%r multiply %r %r" % (self.urls, a, b)
        return a*b

    @rpc_method
    def divide(self, a, b):
        print "%r divide %r %r" % (self.urls, a, b)
        return a/b


if __name__ == '__main__':
    # Multiple RPCService instances can be run in a single process

    # Custom serializer/deserializer functions can be passed in. The server
    # side ones must match.
    echo = Echo(serializer=JSONSerializer())
    echo.bind('tcp://127.0.0.1:5555')
    # We create two Math services to simulate load balancing. A client can
    # connect to both of these services and requests will be load balanced.
    math1 = Math()
    math2 = Math()
    math1.bind('tcp://127.0.0.1:5556')
    math2.bind('tcp://127.0.0.1:5557')
    ioloop.IOLoop.instance().start()
