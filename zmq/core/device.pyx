"""Python binding for 0MQ device function."""

#
#    Copyright (c) 2010-2011 Brian E. Granger & Min Ragan-Kelley
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

from libzmq cimport *
from zmq.core.socket cimport Socket as cSocket
from zmq.core.error import ZMQError

#-----------------------------------------------------------------------------
# Basic device API
#-----------------------------------------------------------------------------

def device(int device_type, cSocket isocket, cSocket osocket):
    """device(device_type, isocket, osocket)

    Start a zeromq device.

    Parameters
    ----------
    device_type : (QUEUE, FORWARDER, STREAMER)
        The type of device to start.
    isocket : Socket
        The Socket instance for the incoming traffic.
    osocket : Socket
        The Socket instance for the outbound traffic.
    """
    cdef int rc = 0
    with nogil:
        if ZMQ_VERSION_MAJOR >= 3:
            rc = c_device(isocket.handle, osocket.handle)
        else:
            rc = zmq_device(device_type, isocket.handle, osocket.handle)
    if rc < 0:
        raise ZMQError()
    return rc

# inner loop inlined, to prevent code duplication for up/downstream
cdef inline int _relay(void * insocket, void *outsocket, zmq_msg_t msg) nogil:
    cdef int more=0
    cdef int label=0
    cdef int flags=0
    cdef size_t flagsz
    flagsz = sizeof (more)

    while (True):

        rc = zmq_recvmsg(insocket, &msg, 0)
        if (rc < 0):
            return -1

        flags = 0
        rc = zmq_getsockopt(insocket, ZMQ_RCVMORE, &more, &flagsz)
        if (rc < 0):
            return -1
        if more:
            flags = flags | ZMQ_SNDMORE
        
        # LABELs have been removed:
        # rc = zmq_getsockopt(insocket, ZMQ_RCVLABEL, &label, &flagsz)
        # if (rc < 0):
        #     return -1
        # if label:
        #     flags = flags | ZMQ_SNDLABEL
        
        rc = zmq_sendmsg(outsocket, &msg, flags)

        if (rc < 0):
            return -1

        if not (flags):
            break
    return 0

# c_device copied (and cythonized) from zmq_device in zeromq release-2.1.6
# used under LGPL
cdef inline int c_device (void * insocket, void *outsocket) nogil:
    if ZMQ_VERSION_MAJOR < 3:
        # shouldn't get here
        return -1
    cdef zmq_msg_t msg
    cdef int rc = zmq_msg_init (&msg)

    if (rc != 0):
        return -1

    cdef zmq_pollitem_t items [2]
    items [0].socket = insocket
    items [0].fd = 0
    items [0].events = ZMQ_POLLIN
    items [0].revents = 0
    items [1].socket = outsocket
    items [1].fd = 0
    items [1].events = ZMQ_POLLIN
    items [1].revents = 0

    while (True):

        #  Wait while there are either requests or replies to process.
        rc = zmq_poll (&items [0], 2, -1)
        if (rc < 0):
            return -1
        

        #  The algorithm below asumes ratio of request and replies processed
        #  under full load to be 1:1. Although processing requests replies
        #  first is tempting it is suspectible to DoS attacks (overloading
        #  the system with unsolicited replies).

        #  Process a request.
        if (items [0].revents & ZMQ_POLLIN):
            rc = _relay(insocket, outsocket, msg)

        #  Process a reply.
        if (items [1].revents & ZMQ_POLLIN):
            rc = _relay(outsocket, insocket, msg)
    return 0


__all__ = ['device']

