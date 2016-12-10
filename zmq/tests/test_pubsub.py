# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


from random import Random
import time
from unittest import TestCase

import zmq

from zmq.tests import BaseZMQTestCase, have_gevent, GreenTest


class TestPubSub(BaseZMQTestCase):

    pass

    # We are disabling this test while an issue is being resolved.
    def test_basic(self):
        s1, s2 = self.create_bound_pair(zmq.PUB, zmq.SUB)
        s2.setsockopt(zmq.SUBSCRIBE, b'')
        time.sleep(0.1)
        msg1 = b'message'
        s1.send(msg1)
        msg2 = s2.recv()  # This is blocking!
        self.assertEqual(msg1, msg2)

    def test_topic(self):
        s1, s2 = self.create_bound_pair(zmq.PUB, zmq.SUB)
        s2.setsockopt(zmq.SUBSCRIBE, b'x')
        time.sleep(0.1)
        msg1 = b'message'
        s1.send(msg1)
        self.assertRaisesErrno(zmq.EAGAIN, s2.recv, zmq.NOBLOCK)
        msg1 = b'xmessage'
        s1.send(msg1)
        msg2 = s2.recv()
        self.assertEqual(msg1, msg2)

if have_gevent:
    class TestPubSubGreen(GreenTest, TestPubSub):

        def create_sub(self, interface='tcp://127.0.0.1'):
            sub = self.context.socket(zmq.SUB)
            sub.setsockopt(zmq.LINGER, 0)
            port = sub.bind_to_random_port(interface)
            addr = '%s:%s' % (interface, port)
            return sub, addr

        def test_sigabrt_issue(self, random=Random(42)):
            import gevent
            pub = self.context.socket(zmq.PUB)
            pub.setsockopt(zmq.LINGER, 0)
            self.sockets.append(pub)
            topics = [str(random.random())[2:] for x in range(10000)]
            def workload(sub):
                subscribed = set()
                # Many subscriptions, for example above 5000, are
                # raising up reproducibility of the crash.
                for x in range(10000):
                    if not subscribed or random.random() < 0.9:
                        topic = random.choice(topics)
                        subscribed.add(topic)
                        sub.set(zmq.SUBSCRIBE, topic)
                    else:
                        topic = random.choice(list(subscribed))
                        subscribed.remove(topic)
                        sub.set(zmq.UNSUBSCRIBE, topic)
                    # Sleeping with gevent for 0 seconds is necessary
                    # to reproduce the crash.
                    gevent.sleep(0)
            for x in range(3):
                sub, addr = self.create_sub()
                pub.connect(addr)
                workload(sub)
                # Only SUB socket closes.  If PUB socket disconnects,
                # the crash won't be reproduced.
                sub.close()
