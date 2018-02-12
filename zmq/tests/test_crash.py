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
        if p.exitcode == 1:
            raise AssertionError('Test failed')
        assert_exit_code(p.exitcode)
    return wrapped


class TestPubSubCrash(BaseZMQTestCase):

    sleep = staticmethod(time.sleep)
    poller = zmq.Poller

    def create_sub(self, interface='tcp://127.0.0.1'):
        sub = self.socket(zmq.SUB)
        # Lower high water mark leads the crash faster.
        sub.set(zmq.SNDHWM, 10)
        port = sub.bind_to_random_port(interface)
        addr = '%s:%s' % (interface, port)
        return sub, addr

    @classmethod
    def _workload(cls, subs, random, n=10000, timeout=5):
        """A workload on SUB sockets which indicates issue #950.

        .. seealso:: https://github.com/zeromq/pyzmq/issues/950

        """
        # Many subscriptions, for example above 5000, are raising up
        # reproducibility of the crash.  Unbalanced and duplicated
        # SUBSCRIBE/UNSUBSCRIBE is the key of the crash.
        started_at = time.time()
        while True:
            for sub in subs:
                t = topic(random.randrange(n))
                if random.random() < 0.5:
                    sub.set(zmq.SUBSCRIBE, t)
                else:
                    sub.set(zmq.UNSUBSCRIBE, t)
                # Sleeping with gevent for 0 seconds is necessary
                # to reproduce the crash.
                cls.sleep(0)
            if time.time() - started_at > timeout:
                return

    @capture_crash
    def test_inconsistent_subscriptions(self, random=Random(42)):
        """https://github.com/zeromq/pyzmq/issues/950"""
        pub = self.socket(zmq.PUB)
        sub1, addr1 = self.create_sub()
        sub2, addr2 = self.create_sub()
        pub.connect(addr1)
        pub.connect(addr2)
        # Here was a crash:
        # Assertion failed: erased == 1 (src/mtrie.cpp:297)
        self._workload([sub1, sub2], random, timeout=5)

    @capture_crash
    def test_close_sub_sockets(self, random=Random(42)):
        pub = self.socket(zmq.PUB)
        pub.setsockopt(zmq.LINGER, 0)
        for x in range(3):
            sub, addr = self.create_sub()
            pub.connect(addr)
            self._workload([sub], random, timeout=5)
            # Only SUB socket closes.  If PUB socket disconnects,
            # the crash won't be reproduced.
            sub.close()


if have_gevent:
    import gevent
    class TestPubSubCrashGreen(GreenTest, TestPubSubCrash):
        sleep = staticmethod(gevent.sleep)
        poller = zmq.green.Poller
