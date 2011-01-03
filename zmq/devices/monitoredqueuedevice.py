"""MonitoredQueue classes and functions.

Authors
-------
* MinRK
* Brian Granger
"""

#
#    Copyright (c) 2010 Min Ragan-Kelley, Brian Granger
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


import time

from zmq.core import XREP, QUEUE, FORWARDER, ZMQError
from zmq.devices.basedevice import Device,ThreadDevice,ProcessDevice
from zmq.devices.monitoredqueue import monitored_queue

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class MonitoredQueueBase(object):
    """Base class for overriding methods."""
    
    def __init__(self, in_type, out_type, mon_type, in_prefix='in', out_prefix='out'):
        
        Device.__init__(self, QUEUE, in_type, out_type)
        
        self.mon_type = mon_type
        self._mon_binds = list()
        self._mon_connects = list()
        self._mon_sockopts = list()
        
        self._in_prefix = in_prefix
        self._out_prefix = out_prefix

    def bind_mon(self, addr):
        """Enqueue ZMQ address for binding on mon_socket.

        See zmq.Socket.bind for details.
        """
        self._mon_binds.append(addr)

    def connect_mon(self, addr):
        """Enqueue ZMQ address for connecting on mon_socket.

        See zmq.Socket.bind for details.
        """
        self._mon_connects.append(addr)

    def setsockopt_mon(self, opt, value):
        """Enqueue setsockopt(opt, value) for mon_socket

        See zmq.Socket.setsockopt for details.
        """
        self._mon_sockopts.append((opt, value))

    def _setup_sockets(self):
        ins,outs = Device._setup_sockets(self)
        ctx = self._context
        mons = ctx.socket(self.mon_type)
        
        # set sockopts (must be done first, in case of zmq.IDENTITY)
        for opt,value in self._mon_sockopts:
            mons.setsockopt(opt, value)
        
        for iface in self._mon_binds:
            mons.bind(iface)
        
        for iface in self._mon_connects:
            mons.connect(iface)
        
        return ins,outs,mons
    
    def run(self):
        ins,outs,mons = self._setup_sockets()
        rc = monitored_queue(ins, outs, mons, 
            self._in_prefix, self._out_prefix)
        self.done = True
        return rc

class MonitoredQueue(MonitoredQueueBase, Device):
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

class ThreadMonitoredQueue(MonitoredQueueBase, ThreadDevice):
    """MonitoredQueue in a Thread. See MonitoredQueue for more."""
    pass

class ProcessMonitoredQueue(MonitoredQueueBase, ProcessDevice):
    """MonitoredQueue in a Process. See MonitoredQueue for more."""
    pass


__all__ = [
    'MonitoredQueue',
    'ThreadMonitoredQueue',
]
if ProcessDevice is not None:
    __all__.append('ProcessMonitoredQueue')

