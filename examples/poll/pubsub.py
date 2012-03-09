"""A thorough test of polling PUB/SUB sockets."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import time
import zmq

print "Running polling tets for PUB/SUB sockets..."

addr = 'tcp://127.0.0.1:5555'
ctx = zmq.Context()
s1 = ctx.socket(zmq.PUB)
s2 = ctx.socket(zmq.SUB)
s2.setsockopt(zmq.SUBSCRIBE, '')

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
assert not socks.has_key(s2)

# Make sure that s1 stays in POLLOUT after a send.
s1.send('msg1')
socks = dict(poller.poll())
assert socks[s1] == zmq.POLLOUT

# Make sure that s2 is POLLIN after waiting.
time.sleep(0.5)
socks = dict(poller.poll())
assert socks[s2] == zmq.POLLIN

# Make sure that s2 goes into 0 after recv.
s2.recv()
socks = dict(poller.poll())
assert not socks.has_key(s2)

poller.unregister(s1)
poller.unregister(s2)

# Wait for everything to finish.
time.sleep(1.0)

print "Finished."
