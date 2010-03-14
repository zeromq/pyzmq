"""A thorough test of polling P2P sockets."""

import time
import zmq

addr = 'tcp://127.0.0.1:5555'
ctx = zmq.Context(1,1,zmq.POLL)
s1 = ctx.socket(zmq.P2P)
s2 = ctx.socket(zmq.P2P)

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

# Wait for everything to finish.
time.sleep(1.0)