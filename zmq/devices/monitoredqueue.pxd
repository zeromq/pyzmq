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

from zmq.core.socket cimport Socket
from zmq.devices.base cimport Device

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
    cdef public int mon_type  # Socket type for mon_socket, e.g. PUB.
    cdef Socket mon_socket    # mon_socket for monitored_queue.
    cdef list mon_binds       # List of interfaces to bind mons to.
    cdef list mon_connects    # List of interfaces to connect mons to.
    cdef list mon_sockopts    # List of tuples for mon.setsockopt.
    cdef str in_prefix        # prefix added to in_socket messages
    cdef str out_prefix       # prefix added to out_socket messages

