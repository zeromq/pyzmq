"""A simple RPC server that show how to run multiple RPC services."""

#-----------------------------------------------------------------------------
#
#    Copyright (c) 2010 Min Ragan-Kelley, Brian Granger
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
