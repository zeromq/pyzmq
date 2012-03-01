"""A simple RPC client that shows how to do load balancing."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012. Brian Granger, Min Ragan-Kelley  
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from zmq.rpc.simplerpc import RPCServiceProxy, RemoteRPCError, JSONSerializer


if __name__ == '__main__':
    # Custom serializer/deserializer functions can be passed in. The server
    # side ones must match.
    echo = RPCServiceProxy(serializer=JSONSerializer())
    echo.connect('tcp://127.0.0.1:5555')
    print "Echoing: ", echo.echo("Hi there")
    try:
        echo.error()
    except RemoteRPCError, e:
        print "Got a remote exception:"
        print e.ename
        print e.evalue
        print e.traceback

    math = RPCServiceProxy()
    # By connecting to two instances, requests are load balanced.
    math.connect('tcp://127.0.0.1:5556')
    math.connect('tcp://127.0.0.1:5557')
    for i in range(5):
        for j in range(5):
            print "Adding: ", i, j, math.add(i,j)
