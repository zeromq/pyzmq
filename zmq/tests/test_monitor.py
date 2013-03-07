# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Guido Goldstein
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

if sys.version_info[0] >= 3:
    long = int

class TestSocketMonitor(TestCase):
    
    def test_monitor(self):
        """Test monitoring interface for sockets."""
        zmq_ctx = zmq.Context()
        s_rep = zmq_ctx.socket(zmq.REP)
        s_req = zmq_ctx.socket(zmq.REQ)
        s_req.bind("tcp://127.0.0.1:6666")
        # try monitoring the REP socket
        s_rep.monitor("inproc://monitor.rep", 255)
        # create listening socket for monitor
        s_event = zmq_ctx.socket(zmq.PAIR)
        s_event.connect("inproc://monitor.rep")
        # test receive event for connect event
        s_rep.connect("tcp://127.0.0.1:6666")
        m = s_event.recv()
        self.assertEqual(m[0], ZMQ_EVENT_CONNECT_DELAYED)
        # test receive event for disconnect event
        s_rep.disconnect("tcp://127.0.0.1:6666")
        m = s_event.recv()
        self.assertEqual(m[0], ZMQ_EVENT_CLOSED)
