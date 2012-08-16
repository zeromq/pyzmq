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
from threading import Thread, Event

import zmq
from zmq.tests import BaseZMQTestCase, have_gevent, GreenTest, skip_green
from zmq.tests import BaseZMQTestCase


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestContext(BaseZMQTestCase):

    def test_set_callback(self):
        global events
        events = 0

        def callback(event, data):
            global events
            events |= event

        ctx = self.Context()
        ctx.set_monitor(callback)

        s = ctx.socket(zmq.REP)
        s.bind_to_random_port('tcp://127.0.0.1')

        time.sleep(0.01)
        assert events & zmq.EVENT_LISTENING
