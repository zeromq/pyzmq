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
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import time
from unittest import TestCase

import zmq
from zmq.utils.strtypes import asbytes
from zmq.tests import PollZMQTestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
def wait():
    time.sleep(.25)


class TestPoll(PollZMQTestCase):

    # This test is failing due to this issue:
    # http://github.com/sustrik/zeromq2/issues#issue/26
    def test_pair(self):
        s1, s2 = self.create_bound_pair(zmq.PAIR, zmq.PAIR)

        # Sleep to allow sockets to connect.
        wait()

        poller = zmq.Poller()
        poller.register(s1, zmq.POLLIN|zmq.POLLOUT)
        poller.register(s2, zmq.POLLIN|zmq.POLLOUT)
        # Poll result should contain both sockets
        socks = dict(poller.poll())
        # Now make sure that both are send ready.
        self.assertEquals(socks[s1], zmq.POLLOUT)
        self.assertEquals(socks[s2], zmq.POLLOUT)
        # Now do a send on both, wait and test for zmq.POLLOUT|zmq.POLLIN
        s1.send(asbytes('msg1'))
        s2.send(asbytes('msg2'))
        wait()
        socks = dict(poller.poll())
        self.assertEquals(socks[s1], zmq.POLLOUT|zmq.POLLIN)
        self.assertEquals(socks[s2], zmq.POLLOUT|zmq.POLLIN)
        # Make sure that both are in POLLOUT after recv.
        s1.recv()
        s2.recv()
        socks = dict(poller.poll())
        self.assertEquals(socks[s1], zmq.POLLOUT)
        self.assertEquals(socks[s2], zmq.POLLOUT)

        poller.unregister(s1)
        poller.unregister(s2)

        # Wait for everything to finish.
        wait()

    def test_reqrep(self):
        s1, s2 = self.create_bound_pair(zmq.REP, zmq.REQ)

        # Sleep to allow sockets to connect.
        wait()

        poller = zmq.Poller()
        poller.register(s1, zmq.POLLIN|zmq.POLLOUT)
        poller.register(s2, zmq.POLLIN|zmq.POLLOUT)

        # Make sure that s1 is in state 0 and s2 is in POLLOUT
        socks = dict(poller.poll())
        self.assertEquals(s1 in socks, 0)
        self.assertEquals(socks[s2], zmq.POLLOUT)

        # Make sure that s2 goes immediately into state 0 after send.
        s2.send(asbytes('msg1'))
        socks = dict(poller.poll())
        self.assertEquals(s2 in socks, 0)

        # Make sure that s1 goes into POLLIN state after a time.sleep().
        time.sleep(0.5)
        socks = dict(poller.poll())
        self.assertEquals(socks[s1], zmq.POLLIN)

        # Make sure that s1 goes into POLLOUT after recv.
        s1.recv()
        socks = dict(poller.poll())
        self.assertEquals(socks[s1], zmq.POLLOUT)

        # Make sure s1 goes into state 0 after send.
        s1.send(asbytes('msg2'))
        socks = dict(poller.poll())
        self.assertEquals(s1 in socks, 0)

        # Wait and then see that s2 is in POLLIN.
        time.sleep(0.5)
        socks = dict(poller.poll())
        self.assertEquals(socks[s2], zmq.POLLIN)

        # Make sure that s2 is in POLLOUT after recv.
        s2.recv()
        socks = dict(poller.poll())
        self.assertEquals(socks[s2], zmq.POLLOUT)

        poller.unregister(s1)
        poller.unregister(s2)

        # Wait for everything to finish.
        wait()
    
    def test_no_events(self):
        s1, s2 = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        poller = zmq.Poller()
        poller.register(s1, zmq.POLLIN|zmq.POLLOUT)
        poller.register(s2, 0)
        self.assertTrue(s1 in poller.sockets)
        self.assertFalse(s2 in poller.sockets)
        poller.register(s1, 0)
        self.assertFalse(s1 in poller.sockets)

    def test_pubsub(self):
        s1, s2 = self.create_bound_pair(zmq.PUB, zmq.SUB)
        s2.setsockopt(zmq.SUBSCRIBE, asbytes(''))

        # Sleep to allow sockets to connect.
        wait()

        poller = zmq.Poller()
        poller.register(s1, zmq.POLLIN|zmq.POLLOUT)
        poller.register(s2, zmq.POLLIN)

        # Now make sure that both are send ready.
        socks = dict(poller.poll())
        self.assertEquals(socks[s1], zmq.POLLOUT)
        self.assertEquals(s2 in socks, 0)
        # Make sure that s1 stays in POLLOUT after a send.
        s1.send(asbytes('msg1'))
        socks = dict(poller.poll())
        self.assertEquals(socks[s1], zmq.POLLOUT)

        # Make sure that s2 is POLLIN after waiting.
        wait()
        socks = dict(poller.poll())
        self.assertEquals(socks[s2], zmq.POLLIN)

        # Make sure that s2 goes into 0 after recv.
        s2.recv()
        socks = dict(poller.poll())
        self.assertEquals(s2 in socks, 0)

        poller.unregister(s1)
        poller.unregister(s2)

        # Wait for everything to finish.
        wait()

class TestSelect(PollZMQTestCase):

    # This test is failing due to this issue:
    # http://github.com/sustrik/zeromq2/issues#issue/26
    def test_pair(self):
        s1, s2 = self.create_bound_pair(zmq.PAIR, zmq.PAIR)

        # Sleep to allow sockets to connect.
        wait()

        rlist, wlist, xlist = zmq.select([s1, s2], [s1, s2], [s1, s2])
        self.assert_(s1 in wlist)
        self.assert_(s2 in wlist)
        self.assert_(s1 not in rlist)
        self.assert_(s2 not in rlist)

