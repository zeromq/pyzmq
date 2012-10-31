# coding: utf-8

from ._cffi import C, ffi, zmq_version, new_uint64_pointer, \
                                        new_int64_pointer, \
                                        new_int_pointer, \
                                        new_binary_data, \
                                        value_uint64_pointer, \
                                        value_int64_pointer, \
                                        value_int_pointer, \
                                        value_binary_data

from ._cffi import strerror

from .constants import *
from .error import *
from .poll import Poller, _poll

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
        self.sockopts = {LINGER: 1}
        self.linger = 1

        global _instance
        _instance = self

    def destroy(self, linger=None):
        self.term(linger=linger)

    def term(self, linger=None):
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

        C.zmq_term(self.zmq_ctx)
        self.zmq_ctx = None
        self._closed = True
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

def new_pointer_from_opt(option, length=0):
    if option in uint64_opts:
        return new_uint64_pointer()
    elif option in int64_opts:
        return new_int64_pointer()
    elif option in int_opts:
        return new_int_pointer()
    elif option in binary_opts:
        return new_binary_data(length)
    else:
        raise ValueError('Invalid option')

def value_from_opt_pointer(option, opt_pointer, length=0):
    if option in uint64_opts:
        return int(opt_pointer[0])
    elif option in int64_opts:
        return int(opt_pointer[0])
    elif option in int_opts:
        return int(opt_pointer[0])
    elif option in binary_opts:
        return ffi.string(opt_pointer)
    else:
        raise ValueError('Invalid option')

def initialize_opt_pointer(option, value, length=0):
    if option in uint64_opts:
        return value_uint64_pointer(value)
    elif option in int64_opts:
        return value_int64_pointer(value)
    elif option in int_opts:
        return value_int_pointer(value)
    elif option in binary_opts:
        return value_binary_data(value, length)
    else:
        raise ValueError('Invalid option')


class Socket(object):
    def __init__(self, context, sock_type):
        self.context = context
        self.sock_type = sock_type
        self.zmq_socket = C.zmq_socket(context.zmq_ctx, sock_type)
        if not self.zmq_socket:
            raise ZMQError()
        self._closed = False
        self._attrs = {}
        self.n = self.context._add_socket(self)
        self.last_errno = None

    @property
    def closed(self):
        return self._closed

    def close(self):
        if not self._closed:
            rc = C.zmq_close(self.zmq_socket)
            self._closed = True
            return rc

    def bind(self, address):
        ret = C.zmq_bind(self.zmq_socket, address)
        if ret != 0:
            raise ZMQError()

    def connect(self, address):
        ret = C.zmq_connect(self.zmq_socket, address)
        return ret

    def setsockopt(self, option, value):
        length = None
        if isinstance(value, str):
            length = len(value)
        low_level_data = initialize_opt_pointer(option, value, length)
        low_level_value_pointer = low_level_data[0]
        low_level_sizet = low_level_data[1]
        ret = C.zmq_setsockopt(self.zmq_socket,
                                option,
                                ffi.cast('void*', low_level_value_pointer),
                                low_level_sizet)
        if option == LINGER:
            self.linger = value

        return ret

    def getsockopt(self, option, length=0):
        low_level_data = new_pointer_from_opt(option, length=length)
        low_level_value_pointer = low_level_data[0]
        low_level_sizet_pointer = low_level_data[1]

        ret = C.zmq_getsockopt(self.zmq_socket,
                               option,
                               low_level_value_pointer,
                               low_level_sizet_pointer)

        if ret < 0:
            self.last_errno = C.zmq_errno()
            return -1

        return value_from_opt_pointer(option, low_level_value_pointer)

    def bind_to_random_port(self, addr,
                                  min_port=49152,
                                  max_port=65536,
                                  max_tries=100):
        for i in range(max_tries):
            try:
                port = random.randrange(min_port, max_port)
                self.bind('%s:%s' % (addr, port))
            except ZMQError as exception:
                if not exception.errno == zmq.EADDRINUSE:
                    raise
            else:
                return port
        raise ZMQBindError("Could not bind socket to random port.")

    def send(self, message, flags=0, copy=False):
        zmq_msg = ffi.new('zmq_msg_t*')

        c_message = ffi.new('char[]', message)
        C.zmq_msg_init_size(zmq_msg, len(message))
        C.strncpy(C.zmq_msg_data(zmq_msg), c_message, len(message))

        if zmq_version == 2:
            ret = C.zmq_send(self.zmq_socket, zmq_msg, flags)
        else:
            ret = C.zmq_sendmsg(self. zmq_socket, zmq_msg, flags)

        C.zmq_msg_close(zmq_msg)
        if ret < 0:
            self.last_errno = C.zmq_errno()

        return ret

    def recv(self, flags=0):
        zmq_msg = ffi.new('zmq_msg_t*')
        C.zmq_msg_init(zmq_msg)

        if zmq_version == 2:
            ret = C.zmq_recv(self.zmq_socket, zmq_msg, flags)
        else:
            ret = C.zmq_recvmsg(self.zmq_socket, zmq_msg, flags)

        if ret < 0:
            C.zmq_msg_close(zmq_msg)
            raise zmqpy.ZMQError(_errno=C.zmq_errno())

        value = ffi.buffer(C.zmq_msg_data(zmq_msg), int(C.zmq_msg_size(zmq_msg)))[:]

        C.zmq_msg_close(zmq_msg)

        return value
