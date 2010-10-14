"""Python binding for 0MQ device function."""

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

from czmq cimport zmq_device
from zmq.core.socket cimport Socket as cSocket

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
    cdef int result = 0
    with nogil:
        result = zmq_device(device_type, isocket.handle, osocket.handle)
    return result


__all__ = ['device']

