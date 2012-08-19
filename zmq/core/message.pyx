"""0MQ Message related classes."""

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

# get version-independent aliases:
cdef extern from "pyversion_compat.h":
    pass

from cpython cimport Py_DECREF, Py_INCREF

from buffers cimport asbuffer_r, viewfromobject_r

cdef extern from "Python.h":
    ctypedef int Py_ssize_t

from libzmq cimport *

import time

try:
    # below 3.3
    from threading import _Event as Event
except (ImportError, AttributeError):
    # python throws ImportError, cython throws AttributeError
    from threading import Event

from zmq.core.error import ZMQError, NotDone
from zmq.utils.strtypes import bytes,unicode,basestring

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


cdef void free_python_msg(void *data, void *hint) with gil:
    """A function for DECREF'ing Python based messages."""
    if hint != NULL:
        tracker_event = (<tuple>hint)[1]
        Py_DECREF(<object>hint)
        if isinstance(tracker_event, Event):
            # don't assert before DECREF:
            # assert tracker_queue.empty(), "somebody else wrote to my Queue!"
            tracker_event.set()
        tracker_event = None

cdef class MessageTracker(object):
    """MessageTracker(*towatch)

    A class for tracking if 0MQ is done using one or more messages.

    When you send a 0MQ mesage, it is not sent immediately. The 0MQ IO thread
    sends the message at some later time. Often you want to know when 0MQ has
    actually sent the message though. This is complicated by the fact that
    a single 0MQ message can be sent multiple times using different sockets.
    This class allows you to track all of the 0MQ usages of a message.

    Parameters
    ----------
    *towatch : tuple of Event, MessageTracker, Message instances.
        This list of objects to track. This class can track the low-level
        Events used by the Message class, other MessageTrackers or
        actual Messages.
    """

    def __init__(self, *towatch):
        """MessageTracker(*towatch)

        Create a message tracker to track a set of mesages.

        Parameters
        ----------
        *towatch : tuple of Event, MessageTracker, Message instances.
            This list of objects to track. This class can track the low-level
            Events used by the Message class, other MessageTrackers or 
            actual Messages.
        """
        self.events = set()
        self.peers = set()
        for obj in towatch:
            if isinstance(obj, Event):
                self.events.add(obj)
            elif isinstance(obj, MessageTracker):
                self.peers.add(obj)
            elif isinstance(obj, Frame):
                if not obj.tracker:
                    raise ValueError("Not a tracked message")
                self.peers.add(obj.tracker)
            else:
                raise TypeError("Require Events or Message Frames, not %s"%type(obj))
    
    @property
    def done(self):
        """Is 0MQ completely done with the message(s) being tracked?"""
        for evt in self.events:
            if not evt.is_set():
                return False
        for pm in self.peers:
            if not pm.done:
                return False
        return True
    
    def wait(self, timeout=-1):
        """mt.wait(timeout=-1)

        Wait for 0MQ to be done with the message or until `timeout`.

        Parameters
        ----------
        timeout : float [default: -1, wait forever]
            Maximum time in (s) to wait before raising NotDone.

        Returns
        -------
        None
            if done before `timeout`
        
        Raises
        ------
        NotDone
            if `timeout` reached before I am done.
        """
        tic = time.time()
        if timeout is False or timeout < 0:
            remaining = 3600*24*7 # a week
        else:
            remaining = timeout
        done = False
        for evt in self.events:
            if remaining < 0:
                raise NotDone
            evt.wait(timeout=remaining)
            if not evt.is_set():
                raise NotDone
            toc = time.time()
            remaining -= (toc-tic)
            tic = toc
        
        for peer in self.peers:
            if remaining < 0:
                raise NotDone
            peer.wait(timeout=remaining)
            toc = time.time()
            remaining -= (toc-tic)
            tic = toc
    
    def old_wait(self):
        """If the new wait works, remove this method."""
        while not self.done:
            time.sleep(.001)


cdef class Frame:
    """Frame(data=None, track=False)

    A zmq message Frame class for non-copy send/recvs.

    This class is only needed if you want to do non-copying send and recvs.
    When you pass a string to this class, like ``Frame(s)``, the 
    ref-count of `s` is increased by two: once because the Frame saves `s` as 
    an instance attribute and another because a ZMQ message is created that
    points to the buffer of `s`. This second ref-count increase makes sure
    that `s` lives until all messages that use it have been sent. Once 0MQ
    sends all the messages and it doesn't need the buffer of s, 0MQ will call
    ``Py_DECREF(s)``.

    Parameters
    ----------

    data : object, optional
        any object that provides the buffer interface will be used to
        construct the 0MQ message data.
    track : bool [default: False]
        whether a MessageTracker_ should be created to track this object.
        Tracking a message has a cost at creation, because it creates a threadsafe
        Event object.
    
    """

    def __cinit__(self, object data=None, track=False, **kwargs):
        cdef int rc
        cdef char *data_c = NULL
        cdef Py_ssize_t data_len_c=0
        cdef object hint

        # init more as False
        self.more = False

        # Save the data object in case the user wants the the data as a str.
        self._data = data
        self._failed_init = True  # bool switch for dealloc
        self._buffer = None       # buffer view of data
        self._bytes = None        # bytes copy of data

        # Event and MessageTracker for monitoring when zmq is done with data:
        if track:
            evt = Event()
            self.tracker_event = evt
            self.tracker = MessageTracker(evt)
        else:
            self.tracker_event = None
            self.tracker = None

        if isinstance(data, unicode):
            raise TypeError("Unicode objects not allowed. Only: str/bytes, buffer interfaces.")

        if data is None:
            with nogil:
                rc = zmq_msg_init(&self.zmq_msg)
            if rc != 0:
                raise ZMQError()
            self._failed_init = False
            return
        else:
            asbuffer_r(data, <void **>&data_c, &data_len_c)
        # We INCREF the *original* Python object (not self) and pass it
        # as the hint below. This allows other copies of this Frame
        # object to take over the ref counting of data properly.
        hint = (data, self.tracker_event)
        Py_INCREF(hint)
        with nogil:
            rc = zmq_msg_init_data(
                &self.zmq_msg, <void *>data_c, data_len_c, 
                <zmq_free_fn *>free_python_msg, <void *>hint
            )
        if rc != 0:
            Py_DECREF(hint)
            raise ZMQError()
        self._failed_init = False
    
    def __init__(self, object data=None, track=False):
        """Enforce signature"""
        pass

    def __dealloc__(self):
        cdef int rc
        if self._failed_init:
            return
        # This simply decreases the 0MQ ref-count of zmq_msg.
        with nogil:
            rc = zmq_msg_close(&self.zmq_msg)
        if rc != 0:
            raise ZMQError()
    
    # buffer interface code adapted from petsc4py by Lisandro Dalcin, a BSD project
    
    def __getbuffer__(self, Py_buffer* buffer, int flags):
        # new-style (memoryview) buffer interface
        with nogil:
            buffer.buf = zmq_msg_data(&self.zmq_msg)
            buffer.len = zmq_msg_size(&self.zmq_msg)
        
        buffer.obj = self
        buffer.readonly = 1
        buffer.format = "B"
        buffer.ndim = 0
        buffer.shape = NULL
        buffer.strides = NULL
        buffer.suboffsets = NULL
        buffer.itemsize = 1
        buffer.internal = NULL
    
    def __getsegcount__(self, Py_ssize_t *lenp):
        # required for getreadbuffer
        if lenp != NULL:
            with nogil:
                lenp[0] = zmq_msg_size(&self.zmq_msg)
        return 1
    
    def __getreadbuffer__(self, Py_ssize_t idx, void **p):
        # old-style (buffer) interface
        cdef char *data_c = NULL
        cdef Py_ssize_t data_len_c
        if idx != 0:
            raise SystemError("accessing non-existent buffer segment")
        # read-only, because we don't want to allow
        # editing of the message in-place
        with nogil:
            data_c = <char *>zmq_msg_data(&self.zmq_msg)
            data_len_c = zmq_msg_size(&self.zmq_msg)
        if p != NULL:
            p[0] = <void*>data_c
        return data_len_c
    
    # end buffer interface
    
    def __copy__(self):
        """Create a shallow copy of the message.

        This does not copy the contents of the Frame, just the pointer.
        This will increment the 0MQ ref count of the message, but not
        the ref count of the Python object. That is only done once when
        the Python is first turned into a 0MQ message.
        """
        return self.fast_copy()

    cdef Frame fast_copy(self):
        """Fast, cdef'd version of shallow copy of the Frame."""
        cdef Frame new_msg
        new_msg = Frame()
        # This does not copy the contents, but just increases the ref-count 
        # of the zmq_msg by one.
        with nogil:
            zmq_msg_copy(&new_msg.zmq_msg, &self.zmq_msg)
        # Copy the ref to data so the copy won't create a copy when str is
        # called.
        if self._data is not None:
            new_msg._data = self._data
        if self._buffer is not None:
            new_msg._buffer = self._buffer
        if self._bytes is not None:
            new_msg._bytes = self._bytes

        # Frame copies share the tracker and tracker_event
        new_msg.tracker_event = self.tracker_event
        new_msg.tracker = self.tracker

        return new_msg

    def __len__(self):
        """Return the length of the message in bytes."""
        cdef int sz
        with nogil:
            sz = zmq_msg_size(&self.zmq_msg)
        return sz
        # return <int>zmq_msg_size(&self.zmq_msg)

    def __str__(self):
        """Return the str form of the message."""
        if isinstance(self._data, bytes):
            b = self._data
        else:
            b = self.bytes
        if str is unicode:
            return b.decode()
        else:
            return b

    cdef inline object _getbuffer(self):
        """Create a Python buffer/view of the message data.

        This will be called only once, the first time the `buffer` property
        is accessed. Subsequent calls use a cached copy.
        """
        if self._data is None:
            return viewfromobject_r(self)
        else:
            return viewfromobject_r(self._data)
    
    @property
    def buffer(self):
        """Get a read-only buffer view of the message contents."""
        if self._buffer is None:
            self._buffer = self._getbuffer()
        return self._buffer

    @property
    def bytes(self):
        """Get the message content as a Python str/bytes object.

        The first time this property is accessed, a copy of the message 
        contents is made. From then on that same copy of the message is
        returned.
        """
        if self._bytes is None:
            self._bytes = copy_zmq_msg_bytes(&self.zmq_msg)
        return self._bytes

# legacy Message name
Message = Frame

__all__ = ['MessageTracker', 'Frame', 'Message']
