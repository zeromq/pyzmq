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
from zmq.tests import PollZMQTestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestPoll(PollZMQTestCase):

    def test_basic(self):
        s1, s2 = self.create_bound_pair(zmq.P2P, zmq.P2P)
        poller = zmq.Poller()
        poller.register(s1)
        poller.register(s2)
        socks = poller.poll()
        for s, mask in socks:
            self.assertEquals(mask, zmq.POLLOUT)
        s1.send('foo')
        s2.send('bar')
        # This sleep of 100 us is needed so that the proceeding sends are
        # carried out and show up in the recv'ing queues.
        time.sleep(0.0001)
        socks = poller.poll()
        for s, mask in socks:
            self.assertEquals(mask, zmq.POLLIN|zmq.POLLOUT)
        s1.recv()
        s2.recv()
        socks = poller.poll()
        for s, mask in socks:
            self.assertEquals(mask, zmq.POLLOUT)
        poller.unregister(s1)
        poller.unregister(s2)

    def test_reqrep(self):
        s1, s2 = self.create_bound_pair(zmq.REQ, zmq.REP)
        poller = zmq.Poller()
        poller.register(s1)
        poller.register(s2)
        socks = poller.poll()
        # I needed this to get rid of an error:
        # Assertion failed: err == ECONNREFUSED || err == ETIMEDOUT (tcp_connecter.cpp:283)
        # Abort trap.
        time.sleep(0.0001)
        for s, mask in socks:
            if s is s1:
                self.assertEquals(mask, zmq.POLLOUT)
            if s is s2:
                self.assertEquals(mask, 0)
        # If I do s1.send('asdf') and then poll I don't get the right
        # flags back. I am getting POLLIN for both.
        poller.unregister(s1)
        poller.unregister(s2)

