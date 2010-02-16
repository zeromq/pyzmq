
from unittest import TestCase

import zmq

class TestContext(TestCase):

    def test_init(self):
        c1 = zmq.Context()
        self.assert_(isinstance(c1, zmq.Context))
        del c1
        c2 = zmq.Context(1,1)
        self.assert_(isinstance(c2, zmq.Context))
        del c2
        c3 = zmq.Context(1,1, zmq.POLL)
        self.assert_(isinstance(c3, zmq.Context))
        del c3

    def test_fail_init(self):
        self.assertRaises(zmq.ZMQError, zmq.Context, 1, -1)
        self.assertRaises(zmq.ZMQError, zmq.Context, 0, 1)

