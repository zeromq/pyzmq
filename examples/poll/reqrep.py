"""A thorough test of polling REQ/REP sockets."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import time
import zmq

print "Running polling tests for REQ/REP sockets..."

addr = 'tcp://127.0.0.1:5555'
ctx = zmq.Context()
s1 = ctx.socket(zmq.REP)
s2 = ctx.socket(zmq.REQ)

s1.bind(addr)
s2.connect(addr)

# Sleep to allow sockets to connect.
time.sleep(1.0)

poller = zmq.Poller()
poller.register(s1, zmq.POLLIN|zmq.POLLOUT)
poller.register(s2, zmq.POLLIN|zmq.POLLOUT)

# Make sure that s1 is in state 0 and s2 is in POLLOUT
socks = dict(poller.poll())
assert not socks.has_key(s1)
assert socks[s2] == zmq.POLLOUT

# Make sure that s2 goes immediately into state 0 after send.
s2.send('msg1')
socks = dict(poller.poll())
assert not socks.has_key(s2)

# Make sure that s1 goes into POLLIN state after a time.sleep().
time.sleep(0.5)
socks = dict(poller.poll())
assert socks[s1] == zmq.POLLIN

# Make sure that s1 goes into POLLOUT after recv.
s1.recv()
socks = dict(poller.poll())
assert socks[s1] == zmq.POLLOUT

# Make sure s1 goes into state 0 after send.
s1.send('msg2')
socks = dict(poller.poll())
assert not socks.has_key(s1)

# Wait and then see that s2 is in POLLIN.
time.sleep(0.5)
socks = dict(poller.poll())
assert socks[s2] == zmq.POLLIN

# Make sure that s2 is in POLLOUT after recv.
s2.recv()
socks = dict(poller.poll())
assert socks[s2] == zmq.POLLOUT

poller.unregister(s1)
poller.unregister(s2)

# Wait for everything to finish.
time.sleep(1.0)

print "Finished."
