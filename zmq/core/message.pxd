"""0MQ Message related class declarations."""

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

from libzmq cimport zmq_msg_t

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

cdef class MessageTracker(object):
    """A class for tracking if 0MQ is done using one or more messages."""

    cdef set events  # Message Event objects to track.
    cdef set peers   # Other Message or MessageTracker objects.
    

cdef class Message:
    """A Message class for non-copy send/recvs."""

    cdef zmq_msg_t zmq_msg
    cdef object _data      # The actual message data as a Python object.
    cdef object _buffer    # A Python Buffer/View of the message contents
    cdef object _bytes     # A bytes/str copy of the message.
    cdef bint _failed_init # Flag to handle failed zmq_msg_init
    cdef public object tracker_event  # Event for use with zmq_free_fn.
    cdef public object tracker        # MessageTracker object.

    cdef Message fast_copy(self) # Create shallow copy of Message object.
    cdef object _getbuffer(self) # Construct self._buffer.

cdef inline object copy_zmq_msg_bytes(zmq_msg_t *zmq_msg)
