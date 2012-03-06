# -*- coding: utf8 -*-
#-----------------------------------------------------------------------------
#  Copyright (c) 2010-2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

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
        self.assertRaises(AssertionError, self.stream.on_recv, 1)
        self.assertRaises(AssertionError, self.stream.on_send, 1)
        self.assertRaises(AssertionError, self.stream.on_recv, zmq)
        
