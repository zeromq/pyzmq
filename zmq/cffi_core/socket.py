# coding: utf-8

from ._cffi import C, ffi, new_uint64_pointer, \
                           new_int64_pointer, \
                           new_int_pointer, \
                           new_binary_data, \
                           value_uint64_pointer, \
                           value_int64_pointer, \
                           value_int_pointer, \
                           value_binary_data, \
                           zmq_major_version, \
                           IPC_PATH_MAX_LEN, \
                           strerror

from .message import Frame
from .constants import *

import zmq
from zmq.error import ZMQError

import random
import codecs

import errno as errno_mod

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
        return ffi.buffer(opt_pointer, length)[:]
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
    context = None
    socket_type = None
    zmq_socket = None
    _closed = None
    n = None
    rcvmore = None

    def __init__(self, context, sock_type):
        self.context = context
        self.socket_type = sock_type
        self.zmq_socket = C.zmq_socket(context.zmq_ctx, sock_type)
        if not self.zmq_socket:
            raise ZMQError(C.zmq_errno())
        self._closed = False
        self.n = self.context._add_socket(self)
        self.rcvmore = False

    @property
    def closed(self):
        return self._closed

    def close(self, linger=None):
        if not self._closed:
            rc = C.zmq_close(self.zmq_socket)
            self._closed = True
            return rc

    def __del__(self):
        self.close()

    def bind(self, address):
        ret = C.zmq_bind(self.zmq_socket, address)
        if ret != 0:
            if IPC_PATH_MAX_LEN and C.zmq_errno() == errno_mod.ENAMETOOLONG:
                # py3compat: address is bytes, but msg wants str
                if str is unicode:
                    address = address.decode('utf-8', 'replace')
                path = address.split('://', 1)[-1]
                msg = ('ipc path "{0}" is longer than {1} '
                                'characters (sizeof(sockaddr_un.sun_path)).'
                                .format(path, IPC_PATH_MAX_LEN))
                raise ZMQError(C.zmq_errno(), msg=msg)
            else:
                raise ZMQError(C.zmq_errno())

    def unbind(self, address):
        ret = C.zmq_unbind(self.zmq_socket, address)

        if ret != 0:
            raise ZMQError(C.zmq_errno())

        return ret

    def connect(self, address):
        ret = C.zmq_connect(self.zmq_socket, address)

        if ret != 0:
            raise ZMQError(C.zmq_errno())

        return ret

    def disconnect(self, address):
        ret = C.zmq_disconnect(self.zmq_socket, address)

        if ret != 0:
            raise ZMQError(C.zmq_errno())

        return ret

    def set(self, option, value):
        length = None
        str_value = False

        if isinstance(value, str):
            length = len(value)
            str_value = True

        try:
            low_level_data = initialize_opt_pointer(option, value, length)
        except ValueError:
            if not str_value:
                raise ZMQError(EINVAL)
            raise TypeError("Invalid Option")

        low_level_value_pointer = low_level_data[0]
        low_level_sizet = low_level_data[1]

        ret = C.zmq_setsockopt(self.zmq_socket,
                               option,
                               ffi.cast('void*', low_level_value_pointer),
                               low_level_sizet)
        if ret < 0:
            raise ZMQError(C.zmq_errno())

        return ret

    def get(self, option, length=0):
        if option in bytes_sockopts:
            length = 255

        try:
            low_level_data = new_pointer_from_opt(option, length=length)
        except ValueError:
            raise ZMQError(EINVAL)

        low_level_value_pointer = low_level_data[0]
        low_level_sizet_pointer = low_level_data[1]

        ret = C.zmq_getsockopt(self.zmq_socket,
                               option,
                               low_level_value_pointer,
                               low_level_sizet_pointer)

        if ret < 0:
            raise ZMQError(C.zmq_errno())

        return value_from_opt_pointer(option, low_level_value_pointer)

    def send(self, message, flags=0, copy=False, track=False):
        if bytes == str and isinstance(message, unicode):
            raise TypeError("Message must be in bytes, not an unicode Object")

        send_frame = False

        if isinstance(message, Frame):
            send_frame = True

        if send_frame:
            zmq_msg = message.zmq_msg
        else:
            zmq_msg = ffi.new('zmq_msg_t*')
            c_message = ffi.new('char[]', message)
            rc = C.zmq_msg_init_size(zmq_msg, len(message))
            C.memcpy(C.zmq_msg_data(zmq_msg), c_message, len(message))

        ret = C.zmq_msg_send(zmq_msg, self._zmq_socket, flags)

        if ret < 0:
            C.zmq_msg_close(zmq_msg)
            raise ZMQError(C.zmq_errno())

        if send_frame:
            if track:
                return zmq.MessageTracker(message)
            return message
        else:
            message = Frame(message, zmq_msg=zmq_msg)
            if track:
                return zmq.MessageTracker(message)
            return message

    def recv(self, flags=0, copy=True, track=False):
        zmq_msg = ffi.new('zmq_msg_t*')
        C.zmq_msg_init(zmq_msg)

        ret = C.zmq_msg_recv(zmq_msg, self._zmq_socket, flags)

        if ret < 0:
            C.zmq_msg_close(zmq_msg)
            raise ZMQError(C.zmq_errno())

        self.rcvmore = self.getsockopt(RCVMORE)

        value = ffi.buffer(C.zmq_msg_data(zmq_msg), C.zmq_msg_size(zmq_msg))[:]

        frame = Frame(value, zmq_msg=zmq_msg)
        frame.more = self.rcvmore

        return frame

__all__ = ['Socket', 'IPC_PATH_MAX_LEN']
