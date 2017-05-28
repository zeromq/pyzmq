"""A simple async RPC client that shows how to do load balancing."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012. Brian Granger, Min Ragan-Kelley  
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from zmq.rpc.simplerpc import AsyncRPCServiceProxy, JSONSerializer
from zmq.eventloop import ioloop
from zmq.utils import jsonapi

def print_result(r):
    print "Got result:", r

def print_error(ename, evalue, tb):
    print "Got error:", ename, evalue
    print tb

if __name__ == '__main__':
    # Custom serializer/deserializer functions can be passed in. The server
    # side ones must match.
    echo = AsyncRPCServiceProxy(serializer=JSONSerializer())
    echo.connect('tcp://127.0.0.1:5555')
    echo.echo(print_result, print_error, 0, "Hi there")

    echo.error(print_result, print_error, 0)
    # Sleep for 2.0s but timeout after 1000ms.
    echo.sleep(print_result, print_error, 1000, 2.0)

    math = AsyncRPCServiceProxy()
    # By connecting to two instances, requests are load balanced.
    math.connect('tcp://127.0.0.1:5556')
    math.connect('tcp://127.0.0.1:5557')
    for i in range(5):
        for j in range(5):
            math.add(print_result, print_error, 0, i,j)
    loop = ioloop.IOLoop.instance()
    loop.start()
