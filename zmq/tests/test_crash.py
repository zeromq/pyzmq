# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import functools
from multiprocessing import Process
import signal
import time

import zmq

from zmq.tests import BaseZMQTestCase, GreenTest, have_gevent


def topic(x):
    """Generates a PUB/SUB topic from a number."""
    return format(x, '08x').encode()


def expect_exit_code(exit_code):
    """Calls a function in a subprocess and checks if the exit code is
    expected.  If you want to verify killing by SIGABRT, try::

       @expect_exit_code(-signal.SIGABRT)
       def test_foo_bar():
           ...

    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            p = Process(target=f, args=args, kwargs=kwargs)
            p.start()
            p.join()
            assert p.exitcode == exit_code
        return wrapped
    return decorator


class TestPubSubCrash(BaseZMQTestCase):

    sleep = staticmethod(time.sleep)
    poller = zmq.Poller

    def create_sub(self, sndhwm, interface='tcp://127.0.0.1'):
        sub = self.socket(zmq.SUB)
        # SNDHWM should be set before bind() on a green socket.
        # Because bind() can synchronize the previous SNDHWM
        # in a very short time.
        sub.set(zmq.SNDHWM, sndhwm)
        port = sub.bind_to_random_port(interface)
        addr = '%s:%s' % (interface, port)
        return sub, addr

    def _many_subscriptions(self, hwm):
        """A low SNDHWM makes a SUB socket drop some subscription messages.
        When a SUB socket drops a subscription message but doesn't drop the
        corresponding unsubscription message, the connected PUB socket will be
        crashed with SIGABRT.

        The workaround is unlimited SUB's SNDHWM and PUB's RCVHWM.  There won't
        be dropped subscriptions.

        .. seealso:: https://github.com/zeromq/libzmq/issues/2942

        """
        pub = self.socket(zmq.PUB)
        pub.set(zmq.RCVHWM, hwm)

        for x in range(100):
            sub, addr = self.create_sub(sndhwm=hwm)

            # Subscriptions before connecting will be processed at once.
            # They have more change to be dropped due to the HWM.
            for x in range(10000):
                sub.set(zmq.SUBSCRIBE, topic(x))

            pub.connect(addr)

            # Getting zmq.EVENTS flushes queued messages.
            # This will be helpful to reproduce a crash.
            pub.get(zmq.EVENTS)
            sub.get(zmq.EVENTS)

            # Unsubscriptions after connecting will be processed one by one.
            # They have less change to be dropped due to the HWM.
            for x in range(10000):
                sub.set(zmq.UNSUBSCRIBE, topic(x))
                sub.get(zmq.EVENTS)

    def test_many_subscriptions_with_unlimited_hwm(self):
        self._many_subscriptions(hwm=0)  # 0 means unlimited

    @expect_exit_code(-signal.SIGABRT)
    def test_many_subscriptions_with_low_hwm(self):
        self._many_subscriptions(hwm=1)  # 1 means just 1 message


if have_gevent:
    import gevent
    class TestPubSubCrashGreen(GreenTest, TestPubSubCrash):
        sleep = staticmethod(gevent.sleep)
        poller = zmq.green.Poller
