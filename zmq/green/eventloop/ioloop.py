from zmq.green import Poller
from zmq.eventloop.ioloop import *

RealIOLoop = IOLoop
RealZMQPoller = ZMQPoller

class IOLoop(RealIOLoop):
    
    def __init__(self, impl=None):
        if impl is None:
            impl = _poll()
        super(IOLoop, self).__init__(impl=impl)

    # these methods are copied verbatim from the real IOLoop
    @staticmethod
    def instance():
        if not hasattr(IOLoop, "_instance"):
            with IOLoop._instance_lock:
                if not hasattr(IOLoop, "_instance"):
                    # New instance after double check
                    IOLoop._instance = IOLoop()
        return IOLoop._instance

    @staticmethod
    def initialized():
        return hasattr(IOLoop, "_instance")

    def install(self):
        assert not IOLoop.initialized()
        IOLoop._instance = self

class ZMQPoller(RealZMQPoller):
    """gevent-compatible version of ioloop.ZMQPoller"""
    def __init__(self):
        self._poller = Poller()

_poll = ZMQPoller
