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

import functools
import sys
import time
from threading import Thread

from unittest import TestCase

import zmq
from zmq.utils import jsonapi

try:
    import gevent
    from zmq import green as gzmq
    have_gevent = True
except ImportError:
    have_gevent = False

try:
    from unittest import SkipTest
except ImportError:
    try:
        from nose import SkipTest
    except ImportError:
        class SkipTest(Exception):
            pass

PYPY = 'PyPy' in sys.version
Iron = 'cli'  in sys.platform

#-----------------------------------------------------------------------------
# skip decorators (directly from unittest)
#-----------------------------------------------------------------------------

_id = lambda x: x

def skip(reason):
    """
    Unconditionally skip a test.
    """
    def decorator(test_item):
        if not (isinstance(test_item, type) and issubclass(test_item, TestCase)):
            @functools.wraps(test_item)
            def skip_wrapper(*args, **kwargs):
                raise SkipTest(reason)
            test_item = skip_wrapper

        test_item.__unittest_skip__ = True
        test_item.__unittest_skip_why__ = reason
        return test_item
    return decorator

def skip_if(condition, reason="Skipped"):
    """
    Skip a test if the condition is true.
    """
    if condition:
        return skip(reason)
    return _id

skip_pypy = skip_if(PYPY, "Doesn't work on PyPy")
skip_iron = skip_if(Iron, "Doesn't work on IronPython")

#-----------------------------------------------------------------------------
# Base test class
#-----------------------------------------------------------------------------

class BaseZMQTestCase(TestCase):
    green = False
    
    @property
    def Context(self):
        if self.green:
            return gzmq.Context
        else:
            return zmq.Context
    
    def socket(self, socket_type):
        s = self.context.socket(socket_type)
        self.sockets.append(s)
        return s
    
    def setUp(self):
        if self.green and not have_gevent:
                raise SkipTest("requires gevent")
        self.context = self.Context.instance()
        self.sockets = []
    
    def tearDown(self):
        contexts = set([self.context])
        while self.sockets:
            sock = self.sockets.pop()
            contexts.add(sock.context) # in case additional contexts are created
            sock.close(0)
        for ctx in contexts:
            t = Thread(target=ctx.term)
            t.daemon = True
            t.start()
            t.join(timeout=2)
            if t.is_alive():
                # reset Context.instance, so the failure to term doesn't corrupt subsequent tests
                zmq.sugar.context.Context._instance = None
                raise RuntimeError("context could not terminate, open sockets likely remain in test")

    def create_bound_pair(self, type1=zmq.PAIR, type2=zmq.PAIR, interface='tcp://127.0.0.1'):
        """Create a bound socket pair using a random port."""
        s1 = self.context.socket(type1)
        s1.setsockopt(zmq.LINGER, 0)
        port = s1.bind_to_random_port(interface)
        s2 = self.context.socket(type2)
        s2.setsockopt(zmq.LINGER, 0)
        s2.connect('%s:%s' % (interface, port))
        self.sockets.extend([s1,s2])
        return s1, s2

    def ping_pong(self, s1, s2, msg):
        s1.send(msg)
        msg2 = s2.recv()
        s2.send(msg2)
        msg3 = s1.recv()
        return msg3

    def ping_pong_json(self, s1, s2, o):
        if jsonapi.jsonmod is None:
            raise SkipTest("No json library")
        s1.send_json(o)
        o2 = s2.recv_json()
        s2.send_json(o2)
        o3 = s1.recv_json()
        return o3

    def ping_pong_pyobj(self, s1, s2, o):
        s1.send_pyobj(o)
        o2 = s2.recv_pyobj()
        s2.send_pyobj(o2)
        o3 = s1.recv_pyobj()
        return o3

    def assertRaisesErrno(self, errno, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except zmq.ZMQError as e:
            self.assertEqual(e.errno, errno, "wrong error raised, expected '%s' \
got '%s'" % (zmq.ZMQError(errno), zmq.ZMQError(e.errno)))
        else:
            self.fail("Function did not raise any error")
    
    def _select_recv(self, multipart, socket, **kwargs):
        """call recv[_multipart] in a way that raises if there is nothing to receive"""
        if zmq.zmq_version_info() >= (3,1,0):
            # zmq 3.1 has a bug, where poll can return false positives,
            # so we wait a little bit just in case
            # See LIBZMQ-280 on JIRA
            time.sleep(0.1)
        
        r,w,x = zmq.select([socket], [], [], timeout=5)
        assert len(r) > 0, "Should have received a message"
        kwargs['flags'] = zmq.DONTWAIT | kwargs.get('flags', 0)
        
        recv = socket.recv_multipart if multipart else socket.recv
        return recv(**kwargs)
        
    def recv(self, socket, **kwargs):
        """call recv in a way that raises if there is nothing to receive"""
        return self._select_recv(False, socket, **kwargs)

    def recv_multipart(self, socket, **kwargs):
        """call recv_multipart in a way that raises if there is nothing to receive"""
        return self._select_recv(True, socket, **kwargs)
    

class PollZMQTestCase(BaseZMQTestCase):
    pass

class GreenTest:
    """Mixin for making green versions of test classes"""
    green = True
    
    def assertRaisesErrno(self, errno, func, *args, **kwargs):
        if errno == zmq.EAGAIN:
            raise SkipTest("Skipping because we're green.")
        try:
            func(*args, **kwargs)
        except zmq.ZMQError:
            e = sys.exc_info()[1]
            self.assertEqual(e.errno, errno, "wrong error raised, expected '%s' \
got '%s'" % (zmq.ZMQError(errno), zmq.ZMQError(e.errno)))
        else:
            self.fail("Function did not raise any error")

    def tearDown(self):
        contexts = set([self.context])
        while self.sockets:
            sock = self.sockets.pop()
            contexts.add(sock.context) # in case additional contexts are created
            sock.close()
        try:
            gevent.joinall([gevent.spawn(ctx.term) for ctx in contexts], timeout=2, raise_error=True)
        except gevent.Timeout:
            raise RuntimeError("context could not terminate, open sockets likely remain in test")
    
    def skip_green(self):
        raise SkipTest("Skipping because we are green")

def skip_green(f):
    def skipping_test(self, *args, **kwargs):
        if self.green:
            raise SkipTest("Skipping because we are green")
        else:
            return f(self, *args, **kwargs)
    return skipping_test
