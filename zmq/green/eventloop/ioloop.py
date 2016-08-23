from zmq.eventloop.ioloop import *
from zmq.green import Poller

RealIOLoop = IOLoop
RealZMQPoller = ZMQPoller

class ZMQPoller(RealZMQPoller):
    """gevent-compatible version of ioloop.ZMQPoller"""
    def __init__(self):
        self._poller = Poller()

class IOLoop(RealIOLoop):
    """gevent-and-zmq-aware tornado IOLoop implementation"""
    _zmq_impl = ZMQPoller

