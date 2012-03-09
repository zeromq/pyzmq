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

import time
from unittest import TestCase

import zmq
from zmq.utils.strtypes import asbytes
from zmq.tests import BaseZMQTestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestPubSub(BaseZMQTestCase):

    pass

    # We are disabling this test while an issue is being resolved.
    def test_basic(self):
        s1, s2 = self.create_bound_pair(zmq.PUB, zmq.SUB)
        s2.setsockopt(zmq.SUBSCRIBE,asbytes(''))
        time.sleep(0.1)
        msg1 = asbytes('message')
        s1.send(msg1)
        msg2 = s2.recv()  # This is blocking!
        self.assertEquals(msg1, msg2)

    def test_topic(self):
        s1, s2 = self.create_bound_pair(zmq.PUB, zmq.SUB)
        s2.setsockopt(zmq.SUBSCRIBE, asbytes('x'))
        time.sleep(0.1)
        msg1 = asbytes('message')
        s1.send(msg1)
        self.assertRaisesErrno(zmq.EAGAIN, s2.recv, zmq.NOBLOCK)
        msg1 = asbytes('xmessage')
        s1.send(msg1)
        msg2 = s2.recv()
        self.assertEquals(msg1, msg2)

