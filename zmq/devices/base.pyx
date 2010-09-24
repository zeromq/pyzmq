"""Classes for running 0MQ Devices in the background.

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

# from cpython cimport bool

# from buffers cimport asbuffer_r

import time
from threading import Thread
from multiprocessing import Process

from zmq import device, ZMQError

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

cdef class Device:
    """A Threadsafe 0MQ Device.
    
    For thread safety, you do not pass Sockets to this, but rather Socket
    types::

        Device(device_type, in_socket_type, out_socket_type)

    For instance::

    dev = Device(zmq.QUEUE, zmq.XREQ, zmq.XREP)

    Similar to zmq.device, but socket types instead of sockets themselves are
    passed, and the sockets are created in the work thread, to avoid issues
    with thread safety. As a result, additional bind_{in|out} and
    connect_{in|out} methods and setsockopt_{in|out} allow users to specify
    connections for the sockets.
    
    Parameters
    ----------
    device_type : int
        The 0MQ Device type
    {in|out}_type : int
        zmq socket types, to be passed later to context.socket(). e.g.
        zmq.PUB, zmq.SUB, zmq.REQ. If out_type is < 0, then in_socket is used
        for both in_socket and out_socket.
        
    Methods
    -------
    bind_{in_out}(iface)
        passthrough for {in|out}_socket.bind(iface), to be called in the thread
    connect_{in_out}(iface)
        passthrough for {in|out}_socket.connect(iface), to be called in the
        thread
    setsockopt_{in_out}(opt,value)
        passthrough for {in|out}_socket.setsockopt(opt, value), to be called in
        the thread
    
    Attributes
    ----------
    daemon: int
        sets whether the thread should be run as a daemon
        Default is true, because if it is false, the thread will not
        exit unless it is killed
    """

    def __init__(self, int device_type, int in_type, int out_type):
        self.device_type = device_type
        self.in_type = in_type
        self.out_type = out_type
        self.in_binds = list()
        self.in_connects = list()
        self.in_sockopts = list()
        self.out_binds = list()
        self.out_connects = list()
        self.out_sockopts = list()
        self.daemon = True
        self.done = False
    
    def bind_in(self, addr):
        """Enqueue ZMQ address for binding on in_socket.

        See ``zmq.Socket.bind`` for details.
        """
        self.in_binds.append(addr)
    
    def connect_in(self, addr):
        """Enqueue ZMQ address for connecting on in_socket.

        See ``zmq.Socket.connect`` for details.
        """
        self.in_connects.append(addr)
    
    def setsockopt_in(self, opt, value):
        """Enqueue setsockopt(opt, value) for in_socket

        See ``zmq.Socket.setsockopt`` for details.
        """
        self.in_sockopts.append((opt, value))
    
    def bind_out(self, iface):
        """Enqueue ZMQ address for binding on out_socket.

        See ``zmq.Socket.bind`` for details.
        """
        self.out_binds.append(iface)
    
    def connect_out(self, iface):
        """Enqueue ZMQ address for connecting on out_socket.

        See ``zmq.Socket.connect`` for details.
        """
        self.out_connects.append(iface)
    
    def setsockopt_out(self, opt, value):
        """Enqueue setsockopt(opt, value) for out_socket

        See ``zmq.Socket.setsockopt`` for details.
        """
        self.out_sockopts.append((opt, value))
    
    def _setup_sockets(self):
        ctx = Context()
        self.context = ctx
        
        # create the sockets
        self.in_socket = ctx.socket(self.in_type)
        if self.out_type < 0:
            self.out_socket = self.in_socket
        else:
            self.out_socket = ctx.socket(self.out_type)
        
        # set sockopts (must be done first, in case of zmq.IDENTITY)
        for opt,value in self.in_sockopts:
            self.in_socket.setsockopt(opt, value)
        for opt,value in self.out_sockopts:
            self.out_socket.setsockopt(opt, value)
        
        for iface in self.in_binds:
            self.in_socket.bind(iface)
        for iface in self.out_binds:
            self.out_socket.bind(iface)
        
        for iface in self.in_connects:
            self.in_socket.connect(iface)
        for iface in self.out_connects:
            self.out_socket.connect(iface)
    
    def run(self):
        """The runner method.

        Do not call me directly, instead call ``self.start()``, just like a
        Thread.
        """
        self._setup_sockets()
        return self._run()
    
    cdef int _run(self):
        cdef int rc = 0
        cdef int device_type = self.device_type
        cdef Socket ins = self.in_socket
        cdef Socket outs = self.out_socket
        rc = device(device_type, ins, outs)
        self.done = True
        return rc
    
    def start(self):
        """Start the device. Override me in subclass for other launchers."""
        return self.run()

    def join(self,timeout=None):
        tic = time.time()
        toc = tic
        while not self.done and not (timeout is not None and toc-tic > timeout):
            time.sleep(.001)
            toc = time.time()


class BackgroundDevice(Device):
    """Base class for launching Devices in background processes and threads."""

    launcher=None
    launch_class=None

    def start(self):
        self.launcher = self.launch_class(target=self.run)
        self.launcher.daemon = self.daemon
        return self.launcher.start()

    def join(self, timeout=None):
        return self.launcher.join(timeout=timeout)

class ThreadDevice(BackgroundDevice):
    """A Device that will be run in a background Thread.

    See `Device` for details.
    """
    launch_class=Thread

class ProcessDevice(BackgroundDevice):
    """A Device that will be run in a background Process.

    See `Device` for details.
    """
    launch_class=Process

