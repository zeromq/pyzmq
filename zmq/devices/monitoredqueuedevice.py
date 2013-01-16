"""MonitoredQueue classes and functions.

Authors
-------
* MinRK
* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


import time

from zmq import ZMQError, PUB
from zmq.devices.proxydevice import ProxyBase, Proxy, ThreadProxy, ProcessProxy
from zmq.devices.monitoredqueue import monitored_queue

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class MonitoredQueueBase(ProxyBase):
    """Base class for overriding methods."""
    
    _in_prefix = b''
    _out_prefix = b''
    
    def __init__(self, in_type, out_type, mon_type=PUB, in_prefix=b'in', out_prefix=b'out'):
        
        ProxyBase.__init__(self, in_type=in_type, out_type=out_type, mon_type=mon_type)
        
        self._in_prefix = in_prefix
        self._out_prefix = out_prefix

    def run(self):
        ins,outs,mons = self._setup_sockets()
        rc = monitored_queue(ins, outs, mons, 
            self._in_prefix, self._out_prefix)
        self.done = True
        return rc

class MonitoredQueue(MonitoredQueueBase, Proxy):
    """Threadsafe MonitoredQueue object.

    *Warning* as with most 'threadsafe' Python objects, this is only
    threadsafe as long as you do not use private methods or attributes.
    Private names are prefixed with '_', such as 'self._setup_socket()'.
    
    See zmq.devices.Device for most of the spec. This subclass adds a
    <method>_mon version of each <method>_{in|out} method, for configuring the
    monitor socket.

    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a
    QUEUE, except each message is also sent out on the monitor socket.

    If a message comes from in_sock, it will be prefixed with 'in'. If it
    comes from out_sock, it will be prefixed with 'out'

    A PUB socket is perhaps the most logical for the mon_socket, but it is not
    restricted.
    """
    pass

class ThreadMonitoredQueue(MonitoredQueueBase, ThreadProxy):
    """MonitoredQueue in a Thread. See MonitoredQueue for more."""
    pass

class ProcessMonitoredQueue(MonitoredQueueBase, ProcessProxy):
    """MonitoredQueue in a Process. See MonitoredQueue for more."""
    pass


__all__ = [
    'MonitoredQueue',
    'ThreadMonitoredQueue',
    'ProcessMonitoredQueue'
]
