"""zmq Cython backend augmented declarations"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from cpython cimport PyBytes_FromStringAndSize

from zmq.backend.cython.libzmq cimport zmq_msg_data, zmq_msg_size, zmq_msg_t


cdef class MessageTracker(object):
    cdef set events  # Message Event objects to track.
    cdef set peers   # Other Message or MessageTracker objects.


cdef class Frame:

    cdef zmq_msg_t zmq_msg
    cdef object _data      # The actual message data as a Python object.
    cdef object _buffer    # A Python memoryview of the message contents
    cdef object _bytes     # A bytes copy of the message.
    cdef bint _failed_init # flag to hold failed init
    cdef public object tracker_event  # Event for use with zmq_free_fn.
    cdef public object tracker        # MessageTracker object.
    cdef public bint more             # whether RCVMORE was set

    cdef Frame fast_copy(self) # Create shallow copy of Message object.
