"""Dummy Frame object"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from ._cffi import ffi, C
import codecs
import time

import zmq

try:
    view = memoryview
except NameError:
    view = buffer

try:
    # below 3.3
    from threading import _Event as Event
except (ImportError):
    from threading import Event

_content = lambda x: x.tobytes() if type(x) == memoryview else x

class Frame(object):
    _data = None
    tracker = None
    closed = False
    more = False
    buffer = None
    
    
    def __init__(self, data, track=False):
        try:
            view(data)
        except TypeError:
            raise

        self._data = data

        if isinstance(data, unicode):
            raise TypeError("Unicode objects not allowed. Only: str/bytes, " +
                            "buffer interfaces.")

        self.more = False
        self.tracker = None
        self.closed = False
        if track:
            self.tracker = zmq.MessageTracker()

        self.buffer = view(self.bytes)

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
        return True

Message = Frame

__all__ = ['Frame', 'Message']
