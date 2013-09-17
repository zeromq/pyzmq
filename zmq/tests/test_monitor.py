# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Guido Goldstein, Min Ragan-Kelley
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
from zmq.tests import BaseZMQTestCase, skip_if, skip_pypy
from zmq.utils.monitor import get_monitor_message


class TestSocketMonitor(BaseZMQTestCase):

    @skip_pypy
    def test_monitor(self):
        """Test monitoring interface for sockets."""
        s_rep = self.context.socket(zmq.REP)
        s_req = self.context.socket(zmq.REQ)
        self.sockets.extend([s_rep, s_req])
        s_req.bind("tcp://127.0.0.1:6666")
        # try monitoring the REP socket
        
        if zmq.zmq_version_info() < (3,2):
            self.assertRaises(NotImplementedError, s_rep.monitor, "inproc://monitor.rep", zmq.EVENT_ALL)
            return
        
        s_rep.monitor("inproc://monitor.rep", zmq.EVENT_ALL)
        # create listening socket for monitor
        s_event = self.context.socket(zmq.PAIR)
        self.sockets.append(s_event)
        s_event.connect("inproc://monitor.rep")
        # test receive event for connect event
        s_rep.connect("tcp://127.0.0.1:6666")
        if zmq.zmq_version_info() < (3,3):
            self.assertRaises(NotImplementedError, get_monitor_message, s_event)
            return
        m = get_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECT_DELAYED)
        self.assertEqual(m['endpoint'], b"tcp://127.0.0.1:6666")
        # test receive event for connected event
        m = get_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECTED)

    @skip_pypy
    def test_monitor_connected(self):
        """Test connected monitoring socket."""
        s_rep = self.context.socket(zmq.REP)
        s_req = self.context.socket(zmq.REQ)
        self.sockets.extend([s_rep, s_req])
        s_req.bind("tcp://127.0.0.1:6667")
        # try monitoring the REP socket
        # create listening socket for monitor
        if zmq.zmq_version_info() < (3,2):
            self.assertRaises(NotImplementedError, s_rep.get_monitor_socket)
            return
        s_event = s_rep.get_monitor_socket()
        self.sockets.append(s_event)
        # test receive event for connect event
        s_rep.connect("tcp://127.0.0.1:6667")
        if zmq.zmq_version_info() < (3,3):
            self.assertRaises(NotImplementedError, get_monitor_message, s_event)
            return
        m = get_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECT_DELAYED)
        self.assertEqual(m['endpoint'], b"tcp://127.0.0.1:6667")
        # test receive event for connected event
        m = get_monitor_message(s_event)
        self.assertEqual(m['event'], zmq.EVENT_CONNECTED)
