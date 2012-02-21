"""A simple RPC client that shows how to do load balancing."""

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
        print e.ename, e.evalue, e.traceback

    math = RPCServiceProxy()
    # By connecting to two instances, requests are load balanced.
    math.connect('tcp://127.0.0.1:5556')
    math.connect('tcp://127.0.0.1:5557')
    for i in range(5):
        for j in range(5):
            print "Adding: ", i, j, math.add(i,j)
