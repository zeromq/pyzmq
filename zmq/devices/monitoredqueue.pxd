"""MonitoredQueue class declarations.

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
from zmq.devices.basedevice cimport Device

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

cdef class MonitoredQueue(Device):
    """Threadsafe MonitoredQueue object."""
    
    cdef public int mon_type  # Socket type for mon_socket, e.g. PUB.
    cdef Socket mon_socket    # mon_socket for monitored_queue.
    cdef list mon_binds       # List of interfaces to bind mons to.
    cdef list mon_connects    # List of interfaces to connect mons to.
    cdef list mon_sockopts    # List of tuples for mon.setsockopt.
    cdef str in_prefix        # prefix added to in_socket messages
    cdef str out_prefix       # prefix added to out_socket messages

