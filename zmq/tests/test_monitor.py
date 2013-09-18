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
import struct

from unittest import TestCase

import zmq
from zmq.tests import BaseZMQTestCase, skip_if
from zmq.utils.monitor import get_monitor_message

skip_version = skip_if(zmq.zmq_version_info()[:2] < (3,3),
                       "Monitoring test skipped due to ZMQ version < 3.3!")

class TestSocketMonitor(BaseZMQTestCase):

    @skip_version
    def test_monitor(self):
        """Test monitoring interface for sockets."""
        zmq_ctx = zmq.Context()
        s_rep = zmq_ctx.socket(zmq.REP)
        s_req = zmq_ctx.socket(zmq.REQ)
        s_req.bind("tcp://127.0.0.1:6666")
        # try monitoring the REP socket
        s_rep.monitor("inproc://monitor.rep", zmq.EVENT_ALL)
        # create listening socket for monitor
        s_event = zmq_ctx.socket(zmq.PAIR)
        s_event.connect("inproc://monitor.rep")
        # test receive event for connect event
        s_rep.connect("tcp://127.0.0.1:6666")
        m = get_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECT_DELAYED)
        self.assertEqual(m['endpoint'], "tcp://127.0.0.1:6666")
        # test receive event for connected event
        m = get_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECTED)

    @skip_version
    def test_monitor_connected(self):
        """Test connected monitoring socket."""
        zmq_ctx = zmq.Context()
        s_rep = zmq_ctx.socket(zmq.REP)
        s_req = zmq_ctx.socket(zmq.REQ)
        s_req.bind("tcp://127.0.0.1:6667")
        # try monitoring the REP socket
        # create listening socket for monitor
        s_event = s_rep.get_monitor_socket()
        # test receive event for connect event
        s_rep.connect("tcp://127.0.0.1:6667")
        m = get_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECT_DELAYED)
        self.assertEqual(m['endpoint'], "tcp://127.0.0.1:6667")
        # test receive event for connected event
        m = get_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECTED)
