# coding: utf-8

from ._cffi import C, ffi, strerror

from .socket import *
from .constants import *

from zmq.error import ZMQError

class Context(object):
    _zmq_ctx = None
    _iothreads = None
    _closed = None
    _n_sockets = None
    _sockets = None

    def __init__(self, io_threads=1):
        if not io_threads > 0:
            raise ZMQError(EINVAL)

        self._zmq_ctx = C.zmq_init(io_threads)
        if self._zmq_ctx== ffi.NULL:
            raise ZMQError(C.zmq_errno())
        self._iothreads = io_threads
        self._closed = False
        self._n_sockets = 0
        self._sockets = {}

    @property
    def closed(self):
        return self._closed

    def _add_socket(self, socket):
        self._sockets[self._n_sockets] = socket
        self._n_sockets += 1

        return self._n_sockets

    def _rm_socket(self, n):
        del self._sockets[n]

    def term(self, linger=None):
        if self.closed:
            return

        for k, s in self._sockets.items():
            if not s.closed:
                if linger:
                    s.setsockopt(LINGER, linger)

        C.zmq_term(self._zmq_ctx)

        self._zmq_ctx = None
        self._closed = True

    def destroy(self, linger=None):
        if self.closed:
            return

        for k, s in self._sockets.items():
            if not s.closed:
                if linger:
                    s.setsockopt(LINGER, linger)
                s.close()

            del self._sockets[k]

        self._n_sockets = 0

    def __del__(self):
        if self._zmq_ctx and not self._closed:
            C.zmq_term(self._zmq_ctx)
            self._zmq_ctx = None
            self._closed = True

__all__ = ['Context']
