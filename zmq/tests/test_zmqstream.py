#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#    Copyright (c) 2011 Brian Granger & Min Ragan-Kelley
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

import sys
import time

from unittest import TestCase

import zmq
from zmq.eventloop import ioloop, zmqstream

class TestZMQStream(TestCase):
    
    def setUp(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.loop = ioloop.IOLoop.instance()
        self.stream = zmqstream.ZMQStream(self.socket)
    
    def tearDown(self):
        self.socket.close()
        self.context.term()
    
    def test_callable_check(self):
        """Ensure callable check works (py3k)."""
        
        self.stream.on_send(lambda *args: None)
        self.stream.on_recv(lambda *args: None)
        self.stream.on_err(lambda *args: None)
        self.assertRaises(AssertionError, self.stream.on_recv, 1)
        self.assertRaises(AssertionError, self.stream.on_send, 1)
        self.assertRaises(AssertionError, self.stream.on_err, 1)
        self.assertRaises(AssertionError, self.stream.on_recv, zmq)
        
