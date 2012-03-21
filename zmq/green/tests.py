import gevent
from zmq.green import zmq

try:
    from gevent_utils import BlockingDetector
    gevent.spawn(BlockingDetector(5))
except ImportError:
    print 'If you encounter hangs consider installing gevent_utils'

def monkey_patch_test_suite():
    """
    Monkey patches parts of pyzmq's test suite to run them with gevent-zeromq.
    """
    zmqtests = __import__('zmq.tests', fromlist=['*', 'test_device', 'test_monqueue'])
    #import ipdb; ipdb.set_trace()
    
    import sys
    try:
        from nose import SkipTest
    except ImportError:
        class SkipTest(Exception):
            pass

    class GreenBaseZMQTestCase(zmqtests.BaseZMQTestCase):
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

    zmqtests.BaseZMQTestCase = GreenBaseZMQTestCase
    
    class BlankTest(GreenBaseZMQTestCase):
        pass

    zmqtests.test_device.TestDevice = BlankTest
    zmqtests.test_monqueue.TestMonitoredQueue = BlankTest
    
