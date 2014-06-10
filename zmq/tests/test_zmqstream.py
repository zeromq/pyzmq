# -*- coding: utf8 -*-
# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


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
        
