# coding: utf-8

from ._cffi import C, ffi, zmq_major_version

from ._cffi import strerror

from .socket import *
from .constants import *
from .error import *

from zmq.utils import jsonapi
import random

_instance = None

class Context(object):
    _state = {}
    def __init__(self, io_threads=1):
        if not io_threads > 0:
            raise ZMQError(EINVAL)

        self.__dict__ = self._state

        self.zmq_ctx = C.zmq_init(io_threads)
        self.iothreads = io_threads
        self._closed = False
        self.n_sockets = 0
        self.max_sockets = 32
        self._sockets = {}
        self.sockopts = {LINGER: -1}

        global _instance
        _instance = self

    def term(self, linger=None):
        if self.closed:
            return

        if zmq_major_version == 2:
            C.zmq_term(self.zmq_ctx)
        else:
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
                elif self.linger:
                    s.setsockopt(LINGER, self.linger)
                s.close()

            del self._sockets[k]

        self.n_sockets = 0

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

    def socket(self, sock_type):
        if self._closed:
            raise ZMQError(ENOTSUP)

        socket = Socket(self, sock_type)
        for option, option_value in self.sockopts.items():
            socket.setsockopt(option, option_value)

        return socket

    def set_linger(self, value):
        self.sockopts[LINGER] = value
        self.linger = value

    def __getattr__(self, attr_name):
        if attr_name == "linger":
            return self.sockopts[LINGER]
        return getattr(self, attr_name)

    def __setattr__(self, attr_name, value):
        if attr_name == "linger":
            self.sockopts[LINGER] = value
        object.__setattr__(self, attr_name, value)

    def __del__(self):
        if zmq_major_version == 2:
            C.zmq_term(self.zmq_ctx)
        else:
            C.zmq_ctx_destroy(self.zmq_ctx)

        self.zmq_ctx = None
        self._closed = True
