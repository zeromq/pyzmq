# coding: utf-8

from ._cffi import C, ffi, strerror

from .socket import *
from .constants import *

from zmq.error import ZMQError

_instance = None

class Context(object):
    zmq_ctx = None
    iothreads = None
    _closed = None
    n_sockets = None
    max_sockets = None
    _sockets = None

    def __init__(self, io_threads=1):
        if not io_threads > 0:
            raise ZMQError(EINVAL)

        self.zmq_ctx = C.zmq_init(io_threads)
        self.iothreads = io_threads
        self._closed = False
        self.n_sockets = 0
        self.max_sockets = 32
        self._sockets = {}

        global _instance
        _instance = self

    @classmethod
    def instance(cls, io_threads=1):
        global _instance
        if _instance is None or _instance.closed:
            _instance = cls(io_threads)
        return _instance

    @property
    def closed(self):
        return self._closed

    def _add_socket(self, socket):
        self._sockets[self.n_sockets] = socket
        self.n_sockets += 1

        return self.n_sockets

    def _rm_socket(self, n):
        del self._sockets[n]

    def term(self, linger=None):
        if self.closed:
            return

        C.zmq_ctx_destroy(self.zmq_ctx)

        self.zmq_ctx = None
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

        self.n_sockets = 0

    def __del__(self):
        if self.zmq_ctx:
            C.zmq_ctx_destroy(self.zmq_ctx)

        self.zmq_ctx = None
        self._closed = True

__all__ = ['Context']
