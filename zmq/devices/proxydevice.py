"""Proxy classes and functions.

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

import zmq
from zmq.devices.basedevice import Device, ThreadDevice, ProcessDevice

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class ProxyBase(object):
    """Base class for overriding methods."""
    
    def __init__(self, in_type, out_type, mon_type=zmq.PUB):
        
        Device.__init__(self, in_type=in_type, out_type=out_type)
        self.mon_type = mon_type
        self._mon_binds = []
        self._mon_connects = []
        self._mon_sockopts = []

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
        rc = zmq.proxy(ins, outs, mons)
        self.done = True
        return rc

class Proxy(ProxyBase, Device):
    """Threadsafe Proxy object.

    *Warning* as with most 'threadsafe' Python objects, this is only
    threadsafe as long as you do not use private methods or attributes.
    Private names are prefixed with '_', such as 'self._setup_socket()'.
    
    See zmq.devices.Device for most of the spec. This subclass adds a
    <method>_mon version of each <method>_{in|out} method, for configuring the
    monitor socket.

    A Proxy is a 3-socket ZMQ Device that functions just like a
    QUEUE, except each message is also sent out on the monitor socket.

    If a message comes from in_sock, it will be prefixed with 'in'. If it
    comes from out_sock, it will be prefixed with 'out'

    A PUB socket is perhaps the most logical for the mon_socket, but it is not
    restricted.
    """
    pass

class ThreadProxy(ProxyBase, ThreadDevice):
    """Proxy in a Thread. See Proxy for more."""
    pass

class ProcessProxy(ProxyBase, ProcessDevice):
    """Proxy in a Process. See Proxy for more."""
    pass


__all__ = [
    'Proxy',
    'ThreadProxy',
    'ProcessProxy',
]
