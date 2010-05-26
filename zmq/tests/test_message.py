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

import copy
from sys import getrefcount as grc
import time
from unittest import TestCase

import zmq
from zmq.tests import PollZMQTestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestMessage(TestCase):

    def test_above_30(self):
        """Message above 30 bytes are never copied by 0MQ."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*'x'
            self.assertEquals(grc(s), 2)
            m = zmq.Message(s)
            self.assertEquals(grc(s), 4)
            del m
            self.assertEquals(grc(s), 2)
            del s

    def test_str(self):
        """Test the str representations of the Messages."""
        for i in range(16):
            s = (2**i)*'x'
            m = zmq.Message(s)
            self.assertEquals(s, str(s))
            self.assert_(s is str(s))

    def test_len(self):
        """Test the len of the Messages."""
        for i in range(16):
            s = (2**i)*'x'
            m = zmq.Message(s)
            self.assertEquals(len(s), len(s))

    def test_lifecycle1(self):
        """Run through a ref counting cycle with a copy."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*'x'
            self.assertEquals(grc(s), 2)
            m = zmq.Message(s)
            self.assertEquals(grc(s), 4)
            m2 = copy.copy(m)
            self.assertEquals(grc(s), 5)
            self.assertEquals(s, str(m))
            self.assertEquals(s, str(m2))
            self.assert_(s is str(m))
            self.assert_(s is str(m2))
            del m2
            self.assertEquals(grc(s), 4)
            del m
            self.assertEquals(grc(s), 2)
            del s

    def test_lifecycle2(self):
        """Run through a different ref counting cycle with a copy."""
        for i in range(5, 16):  # 32, 64,..., 65536
            s = (2**i)*'x'
            self.assertEquals(grc(s), 2)
            m = zmq.Message(s)
            self.assertEquals(grc(s), 4)
            m2 = copy.copy(m)
            self.assertEquals(grc(s), 5)
            self.assertEquals(s, str(m))
            self.assertEquals(s, str(m2))
            self.assert_(s is str(m))
            self.assert_(s is str(m2))
            del m
            self.assertEquals(grc(s), 4)
            del m2
            self.assertEquals(grc(s), 2)
            del s

