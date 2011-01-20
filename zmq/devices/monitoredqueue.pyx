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

cdef extern from "Python.h":
    ctypedef int Py_ssize_t

from buffers cimport asbuffer_r
from czmq cimport *

from zmq.core.socket cimport Socket

from zmq.core import XREP, ZMQError

#-----------------------------------------------------------------------------
# MonitoredQueue functions
#-----------------------------------------------------------------------------


def monitored_queue(Socket in_socket, Socket out_socket, Socket mon_socket,
                    object in_prefix='in', object out_prefix='out'):
    """monitored_queue(in_socket, out_socket, mon_socket,
                       in_prefix='in', out_prefix='out')

    Start a monitored queue device.

    A monitored queue behaves just like a zmq QUEUE device as far as in_socket
    and out_socket are concerned, except that all messages *also* go out on
    mon_socket. mon_socket also prefixes the messages coming from each with a
    prefix, by default 'in' and 'out', so all messages sent by mon_socket are
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
    cdef bint swap_ids
    cdef char *msg_c = NULL
    cdef Py_ssize_t msg_c_len
    cdef int rc

    for prefix in (in_prefix, out_prefix):
        if not isinstance(prefix, bytes):
            raise TypeError("prefix must be bytes, not %s"%type(prefix))

    # force swap_ids if both XREP
    swap_ids = (in_socket.socket_type == XREP and 
                out_socket.socket_type == XREP)
    
    # build zmq_msg objects from str prefixes
    asbuffer_r(in_prefix, <void **>&msg_c, &msg_c_len)
    with nogil:
        rc = zmq_msg_init_size(&in_msg, msg_c_len)
    if rc != 0:
        raise ZMQError()
    with nogil:
        memcpy(zmq_msg_data(&in_msg), msg_c, zmq_msg_size(&in_msg))
    
    asbuffer_r(out_prefix, <void **>&msg_c, &msg_c_len)
    
    with nogil:
        rc = zmq_msg_init_size(&out_msg, msg_c_len)
    if rc != 0:
        raise ZMQError()
    
    with nogil:
        memcpy(zmq_msg_data(&out_msg), msg_c, zmq_msg_size(&out_msg))
        rc = c_monitored_queue(ins, outs, mons, in_msg, out_msg, swap_ids)
    return rc

__all__ = ['monitored_queue']