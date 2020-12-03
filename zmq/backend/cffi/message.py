"""Dummy Frame object"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import errno

from threading import Event

from ._cffi import ffi, lib as C
from .constants import ETERM

import zmq
from zmq.utils.strtypes import unicode
import zmq.error

zmq_gc = None

try:
    from __pypy__.bufferable import bufferable as maybe_bufferable
except ImportError:
    maybe_bufferable = object

_content = lambda x: x.tobytes() if type(x) == memoryview else x


def _check_rc(rc):
    err = C.zmq_errno()
    if rc == -1:
        if err == errno.EINTR:
            raise zmq.error.InterrruptedSystemCall(errno)
        elif errno == errno.EAGAIN:
            raise zmq.error.Again(errno)
        elif errno == ETERM:
            raise zmq.error.ContextTerminated(errno)
        else:
            raise zmq.error.ZMQError(errno)
    return 0


class Frame(maybe_bufferable):
    _data = None
    tracker = None
    closed = False
    more = False
    _buffer = None
    _failed_init = False
    tracker_event = None
    zmq_msg = None

    def __init__(self, data=None, track=False, copy=None, copy_threshold=None):

        self.zmq_msg = ffi.new('zmq_msg_t[1]')

        # self.tracker should start finished
        # except in the case where we are sharing memory with libzmq
        if track:
            self.tracker = zmq._FINISHED_TRACKER

        if isinstance(data, unicode):
            raise TypeError(
                "Unicode objects not allowed. Only: str/bytes, " + "buffer interfaces."
            )

        if data is None:
            rc = C.zmq_msg_init(self.zmq_msg)
            _check_rc(rc)
            self._failed_init = False
            return

        self._data = data

        self._buffer = memoryview(self.bytes)
        data_len_c = self._buffer.nbytes

        if copy is None:
            if copy_threshold and data_len_c < copy_threshold:
                copy = True
            else:
                copy = False

        if copy:
            # copy message data instead of sharing memory
            rc = C.zmq_msg_init_size(self.zmq_msg, data_len_c)
            _check_rc(rc)
            ffi.buffer(C.zmq_msg_data(self.zmq_msg))[:] = self._buffer
            self._failed_init = False
            return

        # Getting here means that we are doing a true zero-copy Frame,
        # where libzmq and Python are sharing memory.
        # Hook up garbage collection with MessageTracker and zmq_free_fn

        # Event and MessageTracker for monitoring when zmq is done with data:
        if track:
            evt = Event()
            self.tracker_event = evt
            self.tracker = zmq.MessageTracker(evt)
        # create the hint for zmq_free_fn
        # two pointers: the zmq_gc context and a message to be sent to the zmq_gc PULL socket
        # allows libzmq to signal to Python when it is done with Python-owned memory.
        global zmq_gc
        if zmq_gc is None:
            from zmq.utils.garbage import gc as zmq_gc
        hint = ffi.new("zhint[1]")
        hint[0].id = zmq_gc.store(data, self.tracker_event)
        if not zmq_gc._push_mutex:
            hint[0].mutex = C.mutex_allocate()
            zmq_gc._push_mutex = hint[0].mutex
        else:
            hint[0].mutex = zmq_gc._push_mutex
        hint[0].sock = ffi.cast("void*", zmq_gc._push_socket.underlying)

        # calls zmq_wrap_msg_init_data with the C.free_python_msg callback
        rc = C.zmq_wrap_msg_init_data(
            self.zmq_msg,
            data,
            data_len_c,
            hint,
        )
        if rc != 0:
            _check_rc(rc)
        self._failed_init = False

    @property
    def buffer(self):
        return self._buffer

    @property
    def bytes(self):
        data = _content(self._data)
        return data

    def __len__(self):
        return len(self.bytes)

    def __eq__(self, other):
        return self.bytes == _content(other)

    def __str__(self):
        if str is unicode:
            return self.bytes.decode()
        else:
            return self.bytes

    @property
    def done(self):
        return self.tracker.done()

    def __buffer__(self, flags):
        return self._buffer


Message = Frame

__all__ = ['Frame', 'Message']
