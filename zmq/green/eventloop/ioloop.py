from zmq.eventloop.ioloop import *
from zmq.green import Poller

RealIOLoop = IOLoop
RealZMQPoller = ZMQPoller

class IOLoop(RealIOLoop):
    
    def __init__(self, impl=None):
        if impl is None:
            impl = _poll()
        super(IOLoop, self).__init__(impl=impl)

    @staticmethod
    def instance():
        """Returns a global `IOLoop` instance.
        
        Most applications have a single, global `IOLoop` running on the
        main thread.  Use this method to get this instance from
        another thread.  To get the current thread's `IOLoop`, use `current()`.
        """
        # install this class as the active IOLoop implementation
        # when using tornado 3
        if tornado_version >= (3,):
            PollIOLoop.configure(IOLoop)
        return PollIOLoop.instance()


class ZMQPoller(RealZMQPoller):
    """gevent-compatible version of ioloop.ZMQPoller"""
    def __init__(self):
        self._poller = Poller()

_poll = ZMQPoller
