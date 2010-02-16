from unittest import TestCase

import zmq

class TestP2P(TestCase):

    def setUp(self):
        self.context = zmq.Context(1,1)

    def test_basic(self):
        s1 = zmq.Socket(self.context, zmq.P2P)
        port = s1.bind_to_random_port('tcp://127.0.0.1')
        s2 = zmq.Socket(self.context, zmq.P2P)
        s2.connect('tcp://127.0.0.1:%s' % port)

        msg1 = 'message 1'
        s1.send(msg1)
        msg2 = s2.recv()
        self.assertEquals(msg1, msg2)

        s2.send(msg1)
        msg2 = s1.recv()
        self.assertEquals(msg1, msg2)

