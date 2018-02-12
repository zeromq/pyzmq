# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import functools
import hashlib
from multiprocessing import Pipe, Process
from random import Random
import time

import pytest

import zmq

from zmq.tests import BaseZMQTestCase, GreenTest, have_gevent


def topic(x):
    """Generates a PUB/SUB topic from a number."""
    return hashlib.md5(str(x)).hexdigest()[:8]


def assert_exit_code(exit_code):
    if exit_code == 1:
        raise AssertionError('Program error')
    elif exit_code == -6:
        raise AssertionError('Crashed by SIGABRT')
    elif exit_code == -11:
        raise AssertionError('Crashed by SIGSEGV')
    elif exit_code < 0:
        raise AssertionError('Crashed with exit code %d' % exit_code)


def capture_crash(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        p = Process(target=f, args=args, kwargs=kwargs)
        p.start()
        p.join()
        assert_exit_code(p.exitcode)
    return wrapped


class TestPubSubCrash(BaseZMQTestCase):

    sleep = staticmethod(time.sleep)
    poller = zmq.Poller

    def create_sub(self, interface='tcp://127.0.0.1'):
        sub = self.socket(zmq.SUB)
        # Lower high water mark leads the crash faster.
        sub.set(zmq.SNDHWM, 1)
        port = sub.bind_to_random_port(interface)
        addr = '%s:%s' % (interface, port)
        return sub, addr

    @capture_crash
    def test_inconsistent_subscriptions(self, random=Random(42)):
        """
        https://github.com/zeromq/pyzmq/issues/950
        https://github.com/zeromq/libzmq/issues/2942
        """
        sub1, addr1 = self.create_sub()
        sub2, addr2 = self.create_sub()

        pub = self.socket(zmq.PUB)
        pub.connect(addr1)
        pub.connect(addr2)

        def workload(subs):
            # Unbalanced and duplicated, so inconsistent SUBSCRIBE/UNSUBSCRIBE
            # is the key of the crash.
            n = 10000
            for x in range(10000):
                for sub in subs:
                    t = topic(random.randrange(n))
                    if random.random() < 0.5:
                        # Same topic should be subscribed multiple times for
                        # the crash.
                        sub.set(zmq.SUBSCRIBE, t)
                    else:
                        # Unsubscribed topics also should be unsubscribed again
                        # for the crash.
                        sub.set(zmq.UNSUBSCRIBE, t)
                    # Sleeping with gevent for 0 seconds is necessary
                    # to reproduce the crash.
                    self.sleep(0)

        # Here was a crash:
        # Assertion failed: erased == 1 (src/mtrie.cpp:297)
        workload([sub1, sub2])

    @capture_crash
    def test_many_subscription_and_unsubscriptions(self):
        """
        https://github.com/zeromq/libzmq/issues/2942
        """
        pub = self.socket(zmq.PUB)

        def workload(sub):
            # Many subscriptions, for example above 5000, are
            # raising up reproducibility of the crash.
            for x in range(10000):
                sub.set(zmq.SUBSCRIBE, topic(x))
            for x in range(10000):
                sub.set(zmq.UNSUBSCRIBE, topic(x))

        for x in range(10):
            sub, addr = self.create_sub()
            # Connection from PUB to SUB indicates this crash.
            pub.connect(addr)
            workload(sub)


if have_gevent:
    import gevent
    class TestPubSubCrashGreen(GreenTest, TestPubSubCrash):
        sleep = staticmethod(gevent.sleep)
        poller = zmq.green.Poller
