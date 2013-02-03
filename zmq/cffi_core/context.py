# coding: utf-8
"""zmq Context class"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import weakref

from ._cffi import C, ffi

from .socket import *
from .constants import *

from zmq.error import ZMQError

class Context(object):
    _zmq_ctx = None
    _iothreads = None
    _closed = None
    _sockets = None

    def __init__(self, io_threads=1):
        if not io_threads >= 0:
            raise ZMQError(EINVAL)

        self._zmq_ctx = C.zmq_init(io_threads)
        if self._zmq_ctx== ffi.NULL:
            raise ZMQError(C.zmq_errno())
        self._iothreads = io_threads
        self._closed = False
        self._sockets = set()

    @property
    def closed(self):
        return self._closed

    def _add_socket(self, socket):
        ref = weakref.ref(socket)
        self._sockets.add(ref)
        return ref

    def _rm_socket(self, ref):
        if ref in self._sockets:
            self._sockets.remove(ref)

    def term(self, linger=None):
        if self.closed:
            return

        sockets = self._sockets
        self._sockets = set()
        for s in sockets:
            s = s()
            if s and not s.closed:
                if linger:
                    s.setsockopt(LINGER, linger)

        C.zmq_term(self._zmq_ctx)

        self._zmq_ctx = None
        self._closed = True

    def destroy(self, linger=None):
        if self.closed:
            return

        sockets = self._sockets
        self._sockets = set()
        for s in sockets:
            s = s()
            if s and not s.closed:
                if linger:
                    s.setsockopt(LINGER, linger)
                s.close()
        
        self.term()

    def __del__(self):
        if self._zmq_ctx and not self._closed:
            C.zmq_term(self._zmq_ctx)
            self._zmq_ctx = None
            self._closed = True

__all__ = ['Context']
