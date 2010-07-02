"""A thorough test of polling PAIR sockets."""

#
#    Copyright (c) 2010 Brian E. Granger
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

import time
import zmq

print "Running polling tests for PAIR sockets..."

addr = 'tcp://127.0.0.1:5555'
ctx = zmq.Context()
s1 = ctx.socket(zmq.PAIR)
s2 = ctx.socket(zmq.PAIR)

s1.bind(addr)
s2.connect(addr)

# Sleep to allow sockets to connect.
time.sleep(1.0)

poller = zmq.Poller()
poller.register(s1, zmq.POLLIN|zmq.POLLOUT)
poller.register(s2, zmq.POLLIN|zmq.POLLOUT)

# Now make sure that both are send ready.
socks = dict(poller.poll())
assert socks[s1] == zmq.POLLOUT
assert socks[s2] == zmq.POLLOUT

# Now do a send on both, wait and test for zmq.POLLOUT|zmq.POLLIN
s1.send('msg1')
s2.send('msg2')
time.sleep(1.0)
socks = dict(poller.poll())
assert socks[s1] == zmq.POLLOUT|zmq.POLLIN
assert socks[s2] == zmq.POLLOUT|zmq.POLLIN

# Make sure that both are in POLLOUT after recv.
s1.recv()
s2.recv()
socks = dict(poller.poll())
assert socks[s1] == zmq.POLLOUT
assert socks[s2] == zmq.POLLOUT

poller.unregister(s1)
poller.unregister(s2)

# Wait for everything to finish.
time.sleep(1.0)

print "Finished."