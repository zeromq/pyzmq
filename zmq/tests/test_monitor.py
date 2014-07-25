# -*- coding: utf-8 -*-
# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import sys
import time
import struct

from unittest import TestCase

import zmq
from zmq.tests import BaseZMQTestCase, skip_if, skip_pypy
from zmq.utils.monitor import recv_monitor_message

skip_lt_4 = skip_if(zmq.zmq_version_info() < (4,), "requires zmq >= 4")

class TestSocketMonitor(BaseZMQTestCase):

    @skip_lt_4
    def test_monitor(self):
        """Test monitoring interface for sockets."""
        s_rep = self.context.socket(zmq.REP)
        s_req = self.context.socket(zmq.REQ)
        self.sockets.extend([s_rep, s_req])
        s_req.bind("tcp://127.0.0.1:6666")
        # try monitoring the REP socket
        
        s_rep.monitor("inproc://monitor.rep", zmq.EVENT_ALL)
        # create listening socket for monitor
        s_event = self.context.socket(zmq.PAIR)
        self.sockets.append(s_event)
        s_event.connect("inproc://monitor.rep")
        s_event.linger = 0
        # test receive event for connect event
        s_rep.connect("tcp://127.0.0.1:6666")
        m = recv_monitor_message(s_event)
        if m['event'] == zmq.EVENT_CONNECT_DELAYED:
            self.assertEqual(m['endpoint'], b"tcp://127.0.0.1:6666")
            # test receive event for connected event
            m = recv_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECTED)
        self.assertEqual(m['endpoint'], b"tcp://127.0.0.1:6666")


    @skip_lt_4
    def test_monitor_connected(self):
        """Test connected monitoring socket."""
        s_rep = self.context.socket(zmq.REP)
        s_req = self.context.socket(zmq.REQ)
        self.sockets.extend([s_rep, s_req])
        s_req.bind("tcp://127.0.0.1:6667")
        # try monitoring the REP socket
        # create listening socket for monitor
        s_event = s_rep.get_monitor_socket()
        s_event.linger = 0
        self.sockets.append(s_event)
        # test receive event for connect event
        s_rep.connect("tcp://127.0.0.1:6667")
        m = recv_monitor_message(s_event)
        if m['event'] == zmq.EVENT_CONNECT_DELAYED:
            self.assertEqual(m['endpoint'], b"tcp://127.0.0.1:6667")
            # test receive event for connected event
            m = recv_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECTED)
        self.assertEqual(m['endpoint'], b"tcp://127.0.0.1:6667")
