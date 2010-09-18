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
from cpython cimport bool

from _zmq cimport *

cdef extern from "Python.h":
    ctypedef int Py_ssize_t
    cdef void PyEval_InitThreads()

# Older versions of Cython would not take care of called this automatically.
# In newer versions of Cython (at least 0.12.1) this is called automatically.
# We should wait for a few releases and then remove this call.
PyEval_InitThreads()

import time
from threading import Thread
from multiprocessing import Process

from zmq import XREP,QUEUE,FORWARDER

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

def monitored_queue(Socket in_socket, Socket out_socket, Socket mon_socket, int swap_ids=False):
    """Start a monitored_queue device"""
    cdef void *ins=in_socket.handle
    cdef void *outs=out_socket.handle
    cdef void *mons=mon_socket.handle
    cdef int rc
    with nogil:
        rc = monitored_queue_(ins, outs, mons, swap_ids)
    return rc

##### end monitored_queue

cdef class Device:
    """A Threadsafe 0MQ Device.
    
    For threadsafety, you do not pass Sockets to this, but rather Socket types:
    
    Device(device_type, in_socket_type, out_socket_type)
    
    For instance:
    
    dev = Device(zmq.QUEUE, zmq.XREQ, zmq.XREP)
    
    Similar to zmq.device, but socket types instead of sockets themselves are passed, and
    the sockets are created in the work thread, to avoid issues with thread safety.
    As a result, additional bind_{in|out} and connect_{in|out} methods and setsockopt_{in|out}
    allow users to specify connections for the sockets.
    
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
    cdef int done
    
    
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
        self.done = False
    
    def __init__(self, int device_type, int in_type, int out_type):
        """force signature"""
    
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
    """Base class for launching Devices in background processes and threads"""
    
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
    
    See `Device` for details."""
    
    launch_class=Thread

class ProcessDevice(BackgroundDevice):
    """A Device that will be run in a background Process.
    
    See `Device` for details."""
    launch_class=Process
    
# cdef class ThreadedDevice(Device):
#     """run a Device in a background Thread. See Device for details.
#     """
#     cdef object thread
#     def start(self):
#         self.thread = Thread(target=self.run)
#         self.thread.daemon = self.daemon
#         return self.thread.start()
#     
#     def join(self, timeout=None):
#         return self.thread.join(timeout)
# 
# class ProcessDevice(Device):
#     """run a Device in a background Process.  See Device for details.
#     """
#     # cdef object process
#     def start(self):
#         self.process = Process(target=self.run)
#         self.process.daemon = self.daemon
#         return self.process.start()
#     
#     def join(self, timeout=None):
#         return self.process.join(timeout)
        
cdef class MonitoredQueue_(Device):
    """Threadsafe MonitoredQueue object. See Device for most of the spec.
    This ignores the device_type, and adds a <method>_mon version of each 
    <method>_{in|out} method, for configuring the monitor socket.
    
    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a QUEUE, 
    except each message is also sent out on the monitor socket.
    
    If a message comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_socket, but it is not restricted.
    
    """
    cdef public int mon_type
    cdef Socket mon_socket
    cdef list mon_binds
    cdef list mon_connects
    cdef list mon_sockopts
    cdef int swap_ids
    
    def __cinit__(self, int device_type, int in_type, int out_type, 
                                    int mon_type, *args, **kwargs):
        self.mon_type = mon_type
        self.mon_binds = list()
        self.mon_connects = list()
        self.mon_sockopts = list()
        if in_type == XREP and out_type == XREP:
            self.swap_ids = 1
        else:
            self.swap_ids = 0
        
    
    def __init__(self, int device_type, int in_type, int out_type, int mon_socket):
        Device.__init__(self, QUEUE, in_type, out_type)
    
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
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        cdef void *mons = self.mon_socket.handle
        with nogil:
            rc = monitored_queue_(ins, outs, mons,self.swap_ids)
        return rc
        
class ThreadMonitoredQueue_(ThreadDevice, MonitoredQueue_):
    pass

class ProcessMonitoredQueue_(ProcessDevice, MonitoredQueue_):
    pass

def MonitoredQueue(int in_type, int out_type, int mon_type):
    """Base Threadsafe MonitoredQueue. See Device for most of the spec.
    This ignores the device_type, and adds a <method>_mon version 
    of each <method>_{in|out} method for configuring the monitor socket.
    
    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a QUEUE,
    except each message is also sent out on the monitor socket.
    
    If a message comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_socket, 
    but it is not restricted.
    
    """
    return MonitoredQueue_(QUEUE, in_type, out_type, mon_type)

def ThreadMonitoredQueue(int in_type, int out_type, int mon_type):
    """Threadsafe MonitoredQueue in a Thread. See Device for most of the spec.
    This ignores the device_type, and adds a <method>_mon version 
    of each <method>_{in|out} method for configuring the monitor socket.
    
    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a QUEUE,
    except each message is also sent out on the monitor socket.
    
    If a message comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_socket, 
    but it is not restricted.
    
    """
    return ThreadMonitoredQueue_(QUEUE, in_type, out_type, mon_type)

def ProcessMonitoredQueue(int in_type, int out_type, int mon_type):
    """MonitoredQueue in a Process. See Device for most of the spec.
    This ignores the device_type, and adds a <method>_mon version 
    of each <method>_{in|out} method for configuring the monitor socket.
    
    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a QUEUE,
    except each message is also sent out on the monitor socket.
    
    If a message comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_socket, 
    but it is not restricted.
    
    """
    return ProcessMonitoredQueue_(QUEUE, in_type, out_type, mon_type)

__all__ = [
    'Device',
    'ThreadDevice',
    'ProcessDevice',
    'MonitoredQueue',
    'ThreadMonitoredQueue',
    'ProcessMonitoredQueue',
    'monitored_queue'
]

