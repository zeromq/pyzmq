"""Python bindings for 0MQ."""

#
#    Copyright (c) 2010 Brian E. Granger
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
# from cpython cimport PyString_FromStringAndSize
# from cpython cimport PyString_AsString, PyString_Size
# from cpython cimport Py_DECREF, Py_INCREF
from cpython cimport bool

# from buffers cimport asbuffer_r, frombuffer_r, viewfromobject_r
from _zmq cimport *
from zmq import XREP,XREQ,REP,REQ,PUB,SUB,QUEUE,FORWARDER
# C constants

cdef extern from "Python.h":
    ctypedef int Py_ssize_t
    cdef void PyEval_InitThreads()

# Older versions of Cython would not take care of called this automatically.
# In newer versions of Cython (at least 0.12.1) this is called automatically.
# We should wait for a few releases and then remove this call.
PyEval_InitThreads()

import time
import random
import struct
import codecs

########### monitored_queue adapted from zmq::queue.cpp #######
# basic free for msg_init_data:
cdef void z_free (void *data, void *hint) nogil:
    free (data)

# the MonitoredQueue C function:
cdef int monitored_queue_ (void *insocket_, void *outsocket_,
                        void *sidesocket_, int swap_ids) nogil:
    
    cdef int ids_done
    cdef zmq_msg_t msg
    cdef int rc = zmq_msg_init (&msg)
    cdef zmq_msg_t id_msg
    rc = zmq_msg_init (&id_msg)
    cdef zmq_msg_t side_msg
    rc = zmq_msg_init (&side_msg)
    cdef zmq_msg_t in_msg
    cdef void *in_data = malloc (2)
    memcpy (in_data, "in", 2)
    rc = zmq_msg_init_data (&in_msg, in_data, 2, z_free, NULL)
    
    cdef zmq_msg_t out_msg
    cdef void *out_data = malloc (3)
    memcpy (out_data, "out", 3)
    rc = zmq_msg_init_data (&out_msg, out_data, 3, z_free, NULL)
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

# def monitored_queue(Socket in_socket,Socket out_socket,Socket mon_socket):
#     """"""
#     cdef void *ins=in_socket.handle
#     cdef void *outs=out_socket.handle
#     cdef void *mons=mon_socket.handle
#     with nogil:
#         sidequeue_(ins, outs, mons)

##### end monitored_queue

import threading
class _DeviceThread(threading.Thread):
    """A wrapped Thread for use in the Device"""
    device = None
    def __init__(self, device):
        threading.Thread.__init__(self)
        self.device = device
        
    def run(self):
        return self.device.run()

cdef class Device:
    """A 0MQ Device.

    Device(device_type, in_socket, out_socket)
    
    Beware, this uses a child thread, but as zmq sockets are not threadsafe,
    if you use the sockets in the main thread after starting the device, 
    odd things might happen. See TSDevice for a threadsafe version

    Parameters
    ----------
    device_type : int
        The 0MQ Device type
    {in|out}_socket : Socket
        ZMQ Sockets for in/out behavior
        
    Attributes
    ----------
    daemon: int
        sets whether the thread should be run as a daemon
        Default is true, because if it is False, the thread will not
        exit unless it is killed

    """
    cdef public int device_type
    cdef public int daemon
    cdef public Socket in_socket
    cdef public Socket out_socket
    
    def __cinit__(self, *args, **kwargs):
        """this is complicated to allow subclassing with different signatures"""
        cdef int i=0
        if isinstance(args[0], int):
            self.device_type = args[0]
            i+=1
        else:
            self.device_type = FORWARDER
        self.in_socket = args[i]
        self.out_socket = args[i+1]
        self.daemon=True
    
    def __init__(self, int device_type, Socket in_socket, Socket out_socket):
        """This is just to force init signature."""
        pass
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef int device_type = self.device_type
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        with nogil:
            rc = zmq_device(device_type, ins, outs)
        return rc
    
    def run(self):
        """The runner method. Do not call me directly, instead call self.start()"""
        return self._run()
    
    def start(self):
        """start the thread"""
        thread = _DeviceThread(self)
        if self.daemon:
            thread.setDaemon(True)
        thread.start()

cdef class MonitoredQueue(Device):
    """A MonitoredQueue 0MQ Device.
    
    mq = MonitoredQueue(in_sock, out_sock, mon_sock)
    
    As far as in_sock and out_sock, this functions exactly the same as
    mq = Device(zmq.QUEUE, in_sock, out_sock)
    
    however, every message relayed through the device is also sent via the mon_sock
    If it comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_sock, but it is not restricted.
    
    For Threadsafe edition, see zmq.TSMonitoredQueue
    
    """
    
    cdef public Socket monitor_socket
    cdef int swap_ids
    
    def __cinit__(self, Socket in_socket, Socket out_socket, Socket monitor_socket, *args, **kwargs):
        self.monitor_socket = monitor_socket
        if in_socket.socket_type == XREP and out_socket.socket_type == XREP:
            self.swap_ids = 1
        else:
            self.swap_ids = 0
        # in_socket/out_socket handled by Device 
    
    def __init__(self, Socket in_socket, Socket out_socket, Socket monitor_socket):
        """This is just to force init signature"""
        Device.__init__(self, QUEUE, in_socket, out_socket)
    #     self.monitor_socket = monitor_socket
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        cdef void *mons = self.monitor_socket.handle
        # cdef int swap_ids
        with nogil:
            rc = monitored_queue_(ins, outs, mons, self.swap_ids)
        return rc

        
cdef class TSDevice:
    """A Threadsafe 0MQ Device.
    It behaves the same as the Device, but creates the sockets as part of the run() command
    
    ThreadsafeDevice(device_type, in_socket_type, out_socket_type)
    
    Similar to Device, but socket types instead of sockets themselves are passed, and
    the sockets are created in the work thread, to avoid issues with thread safety.
    As a result, additional bind_{in|out} and connect_{in|out} methods and setsockopt
    allow users to specify connections for the sockets to be specified
    
    Parameters
    ----------
    device_type : int
        The 0MQ Device type
    {in|out}_type : int
        zmq socket types, to be passed later to context.socket(). e.g. zmq.PUB, zmq.SUB, zmq.REQ.
        If out_type is < 0, then in_socket is used for both in_socket and out_socket.
        
    Methods
    -------
    bind_{in_out}(iface)
        passthrough for {in|out}_socket.bind(iface), to be called in the thread
    connect_{in_out}(iface)
        passthrough for {in|out}_socket.connect(iface), to be called in the thread
    setsockopt_{in_out}(opt,value)
        passthrough for {in|out}_socket.setsockopt(opt, value), to be called in the thread
    
    Attributes
    ----------
    daemon: int
        sets whether the thread should be run as a daemon
        Default is true, because if it is false, the thread will not
        exit unless it is killed
    """
    cdef public int device_type
    cdef public int in_type
    cdef public int out_type
    cdef public int daemon
    cdef Context context
    cdef Socket in_socket
    cdef Socket out_socket
    cdef list in_binds
    cdef list out_binds
    cdef list in_connects
    cdef list out_connects
    cdef list in_sockopts
    cdef list out_sockopts
    
    
    def __cinit__(self, int device_type, int in_type, int out_type, *args, **kwargs):
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
    
    def __init__(self, int device_type, int in_type, int out_type):
        """force signature"""
        pass
    
    # def __deallocate__(self):
    #     del self.in_binds
    #     del self.in_connects
    #     del self.in_sockopts
    #     del self.out_binds
    #     del self.out_connects
    #     del self.out_sockopts
    # 
    def bind_in(self,iface):
        """enqueue interface for binding on in_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.in_binds.append(iface)
    
    def connect_in(self, iface):
        """enqueue interface for connecting on in_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.in_connects.append(iface)
    
    def setsockopt_in(self, opt, value):
        """enqueue setsockopt(opt, value) for in_socket
        e.g. setsockopt_out(zmq.SUBSCRIBE, 'controller')"""
        self.in_sockopts.append((opt, value))
    
    def bind_out(self,iface):
        """enqueue interface for binding on out_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.out_binds.append(iface)
    
    def connect_out(self, iface):
        """enqueue interface for connecting on out_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.out_connects.append(iface)
    
    def setsockopt_out(self, opt, value):
        """"enqueue setsockopt(opt, value) for out_socket
        e.g. setsockopt_out(zmq.IDENTITY, 'alice')"""
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
        """The runner method. Do not call me directly, instead call self.start()"""
        self._setup_sockets()
        return self._run()
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef int device_type = self.device_type
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        with nogil:
            rc = zmq_device(device_type, ins, outs)
        return rc
    
    def start(self):
        """start the thread"""
        thread = _DeviceThread(self)
        if self.daemon:
            thread.setDaemon(True)
        thread.start()
        
cdef class TSMonitoredQueue_(TSDevice):
    """Threadsafe edition of MonitoredQueue. See TSDevice for most of the spec.
    This ignores the device_type
    And adds a <method>_mon version of each <method>_{in|out} method, 
    for configuring the monitor socket.
    
    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a QUEUE, 
    except each message is also sent out on the monitor socket.
    
    If a message comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_socket, but it is not restricted.
    
    For a non-threasafe edition to which you can pass actual Sockets,
    see MonitoredQueue
    
    """
    cdef public int mon_type
    cdef Socket mon_socket
    cdef list mon_binds
    cdef list mon_connects
    cdef list mon_sockopts
    cdef int swap_ids
    
    def __cinit__(self, int device_type, int in_type, int out_type, int mon_type, *args, **kwargs):
        self.mon_type = mon_type
        self.mon_binds = list()
        self.mon_connects = list()
        self.mon_sockopts = list()
        if in_type == XREP and out_type == XREP:
            self.swap_ids = 1
        else:
            self.swap_ids = 0
        
    
    def __init__(self, int device_type, int in_type, int out_type, int mon_socket):
        TSDevice.__init__(self, QUEUE, in_type, out_type)
    
    # def __deallocate__(self):
    #     del self.mon_binds
    #     del self.mon_connects
    #     del self.mon_sockopts
    # 
    def bind_mon(self,iface):
        """enqueue interface for binding on mon_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.mon_binds.append(iface)
    
    def connect_mon(self, iface):
        """enqueue interface for connecting on mon_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.mon_connects.append(iface)
    
    def setsockopt_mon(self, opt, value):
        """"enqueue setsockopt(opt, value) for mon_socket
        e.g. setsockopt_mon(zmq.IDENTITY, 'alice')"""
        self.mon_sockopts.append((opt, value))
    
    def _setup_sockets(self):
        TSDevice._setup_sockets(self)
        ctx = self.context
        self.mon_socket = ctx.socket(self.mon_type)
        
        # set sockopts (must be done first, in case of zmq.IDENTITY)
        for opt,value in self.mon_sockopts:
            self.mon_socket.setsockopt(opt, value)
        
        for iface in self.mon_binds:
            self.mon_socket.bind(iface)
        
        for iface in self.mon_connects:
            self.mon_socket.connect(iface)
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        cdef void *mons = self.mon_socket.handle
        with nogil:
            rc = monitored_queue_(ins, outs, mons,self.swap_ids)
        return rc
        
        
    
def TSMonitoredQueue(int in_type, int out_type, int mon_type):
    """Threadsafe edition of MonitoredQueue. See TSDevice for most of the spec.
    This ignores the device_type
    And adds a <method>_mon version of each <method>_{in|out} method, 
    for configuring the monitor socket.
    
    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a QUEUE, 
    except each message is also sent out on the monitor socket.
    
    If a message comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_socket, but it is not restricted.
    
    For a non-threasafe edition to which you can pass actual Sockets,
    see MonitoredQueue
    
    """
    return TSMonitoredQueue_(QUEUE, in_type, out_type, mon_type)

__all__ = [
    'Device',
    'TSDevice',
    'MonitoredQueue',
    'TSMonitoredQueue',
]

