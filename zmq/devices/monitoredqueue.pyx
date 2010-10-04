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

from libc.stdlib cimport free,malloc
from cpython cimport bool

cdef extern from "Python.h":
    ctypedef int Py_ssize_t

from buffers cimport asbuffer_r
from czmq cimport *
from zmq.devices.basedevice cimport Device

import time
from threading import Thread
from multiprocessing import Process

from zmq.core import XREP, QUEUE, FORWARDER, ZMQError
from zmq.devices.basedevice import ThreadDevice, ProcessDevice

#-----------------------------------------------------------------------------
# MonitoredQueue functions
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

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


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
    'MonitoredQueue',
    'ThreadMonitoredQueue',
    'ProcessMonitoredQueue',
    'monitored_queue'
]

