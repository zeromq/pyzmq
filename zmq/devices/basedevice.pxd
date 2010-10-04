"""Class declarations for running 0MQ Devices in the background.

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

from zmq.core.socket cimport Socket
from zmq.core.context cimport Context

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

cdef class Device:
    """Base Threadsafe 0MQ Device."""
    
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

    cdef int _run(self)         # underlying run method
