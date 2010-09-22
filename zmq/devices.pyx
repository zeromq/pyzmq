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

from libc.stdlib cimport free,malloc
from cpython cimport bool

from _zmq cimport *
from buffers cimport asbuffer_r

cdef extern from "Python.h":
    ctypedef int Py_ssize_t
    cdef void PyEval_InitThreads()

# It seems that in only *some* version of Python/Cython we need to call this
# by hand to get threads initialized. Not clear why this is the case though.
# If we don't have this, pyzmq will segfault.
PyEval_InitThreads()

import time
from threading import Thread
from multiprocessing import Process

from zmq import XREP, QUEUE, FORWARDER, device, ZMQError

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
    cdef public int device_type # ZMQ Device Type.
    cdef public int in_type     # Socket type for in_socket.
    cdef public int out_type    # Socket type for out_socket.
    cdef public int daemon      # Daemon flag, see Thread.daemon.
    cdef Context context        # Context for creating sockets.
    cdef Socket in_socket       # The in_socket passed to zmq.device.
    cdef Socket out_socket      # The out_socket passed to zmq.device.
    cdef list in_binds          # List of interfaces to bind ins to.
    cdef list out_binds         # List of interfaces to bind outs to.
    cdef list in_connects       # List of interfaces to connect ins to.
    cdef list out_connects      # List of interfaces to connect outs to.
    cdef list in_sockopts       # List of tuples for in.setsockopt.
    cdef list out_sockopts      # List of tuples for out.setsockopt.
    cdef int done               # bool flag for when I'm done.

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

#-----------------------------------------------------------------------------
# MonitoredQueue
#-----------------------------------------------------------------------------

# basic free for msg_init_data:
cdef void z_free (void *data, void *hint) nogil:
    free (data)

# the MonitoredQueue C function, adapted from zmq::queue.cpp :
cdef int monitored_queue_ (void *insocket_, void *outsocket_,
                        void *sidesocket_, zmq_msg_t in_msg, 
                        zmq_msg_t out_msg, int swap_ids) nogil:
    """The actual C function for a monitored queue device. 

    See ``monitored_queue()`` for details.
    """

    cdef int ids_done
    cdef zmq_msg_t msg
    cdef int rc = zmq_msg_init (&msg)
    cdef zmq_msg_t id_msg
    rc = zmq_msg_init (&id_msg)
    cdef zmq_msg_t side_msg
    rc = zmq_msg_init (&side_msg)
    # assert (rc == 0)

    cdef int64_t more
    cdef size_t moresz

    cdef zmq_pollitem_t items [2]
    items [0].socket = insocket_
    items [0].fd = 0
    items [0].events = ZMQ_POLLIN
    items [0].revents = 0
    items [1].socket = outsocket_
    items [1].fd = 0
    items [1].events = ZMQ_POLLIN
    items [1].revents = 0
    # I don't think sidesocket should be polled?
    # items [2].socket = sidesocket_
    # items [2].fd = 0
    # items [2].events = ZMQ_POLLIN
    # items [2].revents = 0

    while (True):

        # //  Wait while there are either requests or replies to process.
        rc = zmq_poll (&items [0], 2, -1)
        
        # //  The algorithm below asumes ratio of request and replies processed
        # //  under full load to be 1:1. Although processing requests replies
        # //  first is tempting it is suspectible to DoS attacks (overloading
        # //  the system with unsolicited replies).
        # 
        # //  Process a request.
        if (items [0].revents & ZMQ_POLLIN):
            # send in_prefix to side socket
            rc = zmq_msg_copy(&side_msg, &in_msg)
            rc = zmq_send (sidesocket_, &side_msg, ZMQ_SNDMORE)
            if swap_ids:# both xrep, must send second identity first
                # recv two ids into msg, id_msg
                rc = zmq_recv (insocket_, &msg, 0)
                rc = zmq_recv (insocket_, &id_msg, 0)
                
                # send second id (id_msg) first
                #!!!! always send a copy before the original !!!!
                rc = zmq_msg_copy(&side_msg, &id_msg)
                rc = zmq_send (outsocket_, &side_msg, ZMQ_SNDMORE)
                rc = zmq_send (sidesocket_, &id_msg, ZMQ_SNDMORE)
                # send first id (msg) second
                rc = zmq_msg_copy(&side_msg, &msg)
                rc = zmq_send (outsocket_, &side_msg, ZMQ_SNDMORE)
                rc = zmq_send (sidesocket_, &msg, ZMQ_SNDMORE)
            while (True):
                rc = zmq_recv (insocket_, &msg, 0)
                # assert (rc == 0)

                moresz = sizeof (more)
                rc = zmq_getsockopt (insocket_, ZMQ_RCVMORE, &more, &moresz)
                # assert (rc == 0)

                rc = zmq_msg_copy(&side_msg, &msg)
                if more:
                    rc = zmq_send (outsocket_, &side_msg, ZMQ_SNDMORE)
                    rc = zmq_send (sidesocket_, &msg,ZMQ_SNDMORE)
                else:
                    rc = zmq_send (outsocket_, &side_msg, 0)
                    rc = zmq_send (sidesocket_, &msg,0)
                # assert (rc == 0)

                if (not more):
                    break
        if (items [1].revents & ZMQ_POLLIN):
            rc = zmq_msg_copy(&side_msg, &out_msg)
            rc = zmq_send (sidesocket_, &side_msg, ZMQ_SNDMORE)
            if swap_ids:
                # recv two ids into msg, id_msg
                rc = zmq_recv (outsocket_, &msg, 0)
                rc = zmq_recv (outsocket_, &id_msg, 0)
                
                # send second id (id_msg) first
                rc = zmq_msg_copy(&side_msg, &id_msg)
                rc = zmq_send (insocket_, &side_msg, ZMQ_SNDMORE)
                rc = zmq_send (sidesocket_, &id_msg,ZMQ_SNDMORE)
                
                # send first id (msg) second
                rc = zmq_msg_copy(&side_msg, &msg)
                rc = zmq_send (insocket_, &side_msg, ZMQ_SNDMORE)
                rc = zmq_send (sidesocket_, &msg,ZMQ_SNDMORE)
            while (True):
                rc = zmq_recv (outsocket_, &msg, 0)
                # assert (rc == 0)

                moresz = sizeof (more)
                rc = zmq_getsockopt (outsocket_, ZMQ_RCVMORE, &more, &moresz)
                # assert (rc == 0)
                rc = zmq_msg_copy(&side_msg, &msg)
                if more:
                    rc = zmq_send (insocket_, &side_msg,ZMQ_SNDMORE)
                    rc = zmq_send (sidesocket_, &msg,ZMQ_SNDMORE)
                else:
                    rc = zmq_send (insocket_, &side_msg,0)
                    rc = zmq_send (sidesocket_, &msg,0)
                # errno_assert (rc == 0)

                if (not more):
                    break
    return 0

def monitored_queue(Socket in_socket, Socket out_socket, Socket mon_socket,
                    str in_prefix='in', str out_prefix='out'):
    """Start a monitored queue device.

    A monitored queue behaves just like a zmq QUEUE device as far as in_socket
    and out_socket are concerned, except that all messages *also* go out on
    mon_socket. mon_socket also prefixes the messages coming from each with a
    prefix, by defaout 'in' and 'out', so all messages sent by mon_socket are
    multipart.
    
    The only difference between this and a QUEUE as far as in/out are
    concerned is that it works with two XREP sockets by swapping the IDENT
    prefixes.
    
    Parameters
    ----------
    in_socket : Socket
        One of the sockets to the Queue. Its messages will be prefixed with
        'in'.
    out_socket : Socket
        One of the sockets to the Queue. Its messages will be prefixed with
        'out'. The only difference between in/out socket is this prefix.
    mon_socket : Socket
        This socket sends out every message received by each of the others
        with an in/out prefix specifying which one it was.
    in_prefix : str
        Prefix added to broadcast messages from in_socket.
    out_prefix : str
        Prefix added to broadcast messages from out_socket.
    """
    
    cdef void *ins=in_socket.handle
    cdef void *outs=out_socket.handle
    cdef void *mons=mon_socket.handle
    cdef zmq_msg_t in_msg
    cdef zmq_msg_t out_msg
    cdef bool swap_ids
    cdef char *msg_c = NULL
    cdef Py_ssize_t msg_c_len
    cdef int rc

    # force swap_ids if both XREP
    swap_ids = (in_socket.socket_type == XREP and 
                out_socket.socket_type == XREP)
    
    # build zmq_msg objects from str prefixes
    asbuffer_r(in_prefix, <void **>&msg_c, &msg_c_len)
    rc = zmq_msg_init_size(&in_msg, msg_c_len)
    if rc != 0:
        raise ZMQError()
    memcpy(zmq_msg_data(&in_msg), msg_c, zmq_msg_size(&in_msg))
    
    asbuffer_r(out_prefix, <void **>&msg_c, &msg_c_len)
    rc = zmq_msg_init_size(&out_msg, msg_c_len)
    if rc != 0:
        raise ZMQError()
    memcpy(zmq_msg_data(&out_msg), msg_c, zmq_msg_size(&out_msg))
    
    with nogil:
        rc = monitored_queue_(ins, outs, mons, in_msg, out_msg, swap_ids)
    return rc


cdef class MonitoredQueue(Device):
    """Threadsafe MonitoredQueue object.

    See Device for most of the spec. This ignores the device_type, and adds a
    <method>_mon version of each <method>_{in|out} method, for configuring the
    monitor socket.

    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a
    QUEUE, except each message is also sent out on the monitor socket.

    If a message comes from in_sock, it will be prefixed with 'in'. If it
    comes from out_sock, it will be prefixed with 'out'

    A PUB socket is perhaps the most logical for the mon_socket, but it is not
    restricted.
    """
    cdef public int mon_type  # Socket type for mon_socket, e.g. PUB.
    cdef Socket mon_socket    # mon_socket for monitored_queue.
    cdef list mon_binds       # List of interfaces to bind mons to.
    cdef list mon_connects    # List of interfaces to connect mons to.
    cdef list mon_sockopts    # List of tuples for mon.setsockopt.
    cdef str in_prefix        # prefix added to in_socket messages
    cdef str out_prefix       # prefix added to out_socket messages
    
    def __init__(self, int in_type, int out_type, int mon_type, 
                        str in_prefix='in', str out_prefix='out'):
        Device.__init__(self, QUEUE, in_type, out_type)
        
        self.mon_type = mon_type
        self.mon_binds = list()
        self.mon_connects = list()
        self.mon_sockopts = list()
        self.in_prefix = in_prefix
        self.out_prefix = out_prefix

    def bind_mon(self, addr):
        """Enqueue ZMQ address for binding on mon_socket.

        See ``zmq.Socket.bind`` for details.
        """
        self.mon_binds.append(addr)

    def connect_mon(self, addr):
        """Enqueue ZMQ address for connecting on mon_socket.

        See ``zmq.Socket.bind`` for details.
        """
        self.mon_connects.append(addr)

    def setsockopt_mon(self, opt, value):
        """Enqueue setsockopt(opt, value) for mon_socket

        See ``zmq.Socket.setsockopt`` for details.
        """
        self.mon_sockopts.append((opt, value))

    def _setup_sockets(self):
        Device._setup_sockets(self)
        ctx = self.context
        self.mon_socket = ctx.socket(self.mon_type)
        
        # set sockopts (must be done first, in case of zmq.IDENTITY)
        for opt,value in self.mon_sockopts:
            self.mon_socket.setsockopt(opt, value)
        
        for iface in self.mon_binds:
            self.mon_socket.bind(iface)
        
        for iface in self.mon_connects:
            self.mon_socket.connect(iface)
    
    cdef int _run(self):
        cdef int rc = 0
        cdef Socket ins = self.in_socket
        cdef Socket outs = self.out_socket
        cdef Socket mons = self.mon_socket
        rc = monitored_queue(ins, outs, mons, self.in_prefix, self.out_prefix)
        return rc

class ThreadMonitoredQueue(ThreadDevice, MonitoredQueue):
    """MonitoredQueue in a Thread. See MonitoredQueue for more."""
    pass


class ProcessMonitoredQueue(ProcessDevice, MonitoredQueue):
    """MonitoredQueue in a Process. See MonitoredQueue for more."""
    pass


__all__ = [
    'Device',
    'ThreadDevice',
    'ProcessDevice',
    'MonitoredQueue',
    'ThreadMonitoredQueue',
    'ProcessMonitoredQueue',
    'monitored_queue'
]

