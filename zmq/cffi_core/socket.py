# coding: utf-8
"""zmq Socket class"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import random
import codecs

import errno as errno_mod

from ._cffi import (C, ffi, new_uint64_pointer, new_int64_pointer,
                    new_int_pointer, new_binary_data, value_uint64_pointer,
                    value_int64_pointer, value_int_pointer, value_binary_data,
                    zmq_major_version, IPC_PATH_MAX_LEN)

from .message import Frame
from .constants import *

import zmq
from zmq.error import ZMQError, _check_rc
from zmq.utils.strtypes import unicode


def new_pointer_from_opt(option, length=0):
    from zmq.sugar.constants import int_sockopts,   \
                                    int64_sockopts, \
                                    bytes_sockopts
    if option in int64_sockopts:
        return new_int64_pointer()
    elif option in int_sockopts:
        return new_int_pointer()
    elif option in bytes_sockopts:
        return new_binary_data(length)
    else:
        raise ValueError('Invalid option')

def value_from_opt_pointer(option, opt_pointer, length=0):
    from zmq.sugar.constants import int_sockopts,   \
                                    int64_sockopts, \
                                    bytes_sockopts
    if option in int64_sockopts:
        return int(opt_pointer[0])
    elif option in int_sockopts:
        return int(opt_pointer[0])
    elif option in bytes_sockopts:
        return ffi.buffer(opt_pointer, length)[:]
    else:
        raise ValueError('Invalid option')

def initialize_opt_pointer(option, value, length=0):
    from zmq.sugar.constants import int_sockopts,   \
                                    int64_sockopts, \
                                    bytes_sockopts
    if option in int64_sockopts:
        return value_int64_pointer(value)
    elif option in int_sockopts:
        return value_int_pointer(value)
    elif option in bytes_sockopts:
        return value_binary_data(value, length)
    else:
        raise ValueError('Invalid option')


class Socket(object):
    context = None
    socket_type = None
    _zmq_socket = None
    _closed = None
    _ref = None

    def __init__(self, context, sock_type):
        self.context = context
        self.socket_type = sock_type
        self._zmq_socket = C.zmq_socket(context._zmq_ctx, sock_type)
        if self._zmq_socket == ffi.NULL:
            raise ZMQError()
        self._closed = False
        self._ref = self.context._add_socket(self)

    @property
    def closed(self):
        return self._closed

    def close(self, linger=None):
        rc = 0
        if not self._closed and hasattr(self, '_zmq_socket'):
            if self._zmq_socket is not None:
                rc = C.zmq_close(self._zmq_socket)
            self._closed = True
            self.context._rm_socket(self._ref)
        return rc

    def __del__(self):
        self.close()

    def bind(self, address):
        rc = C.zmq_bind(self._zmq_socket, address)
        if rc < 0:
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
                _check_rc(rc)

    def unbind(self, address):
        rc = C.zmq_unbind(self._zmq_socket, address)
        _check_rc(rc)

    def connect(self, address):
        rc = C.zmq_connect(self._zmq_socket, address)
        _check_rc(rc)

    def disconnect(self, address):
        rc = C.zmq_disconnect(self._zmq_socket, address)
        _check_rc(rc)

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

        rc = C.zmq_setsockopt(self._zmq_socket,
                               option,
                               ffi.cast('void*', low_level_value_pointer),
                               low_level_sizet)
        _check_rc(rc)

    def get(self, option, length=0):
        from zmq.sugar.constants import bytes_sockopts
        if option in bytes_sockopts:
            length = 255

        try:
            low_level_data = new_pointer_from_opt(option, length=length)
        except ValueError:
            raise ZMQError(EINVAL)

        low_level_value_pointer = low_level_data[0]
        low_level_sizet_pointer = low_level_data[1]

        rc = C.zmq_getsockopt(self._zmq_socket,
                               option,
                               low_level_value_pointer,
                               low_level_sizet_pointer)
        _check_rc(rc)

        return value_from_opt_pointer(option, low_level_value_pointer)

    def send(self, message, flags=0, copy=False, track=False):
        if isinstance(message, unicode):
            raise TypeError("Message must be in bytes, not an unicode Object")

        if isinstance(message, Frame):
            message = message.bytes

        zmq_msg = ffi.new('zmq_msg_t*')
        c_message = ffi.new('char[]', message)
        rc = C.zmq_msg_init_size(zmq_msg, len(message))
        C.memcpy(C.zmq_msg_data(zmq_msg), c_message, len(message))

        rc = C.zmq_msg_send(zmq_msg, self._zmq_socket, flags)
        C.zmq_msg_close(zmq_msg)
        _check_rc(rc)

        if track:
            return zmq.MessageTracker()

    def recv(self, flags=0, copy=True, track=False):
        zmq_msg = ffi.new('zmq_msg_t*')
        C.zmq_msg_init(zmq_msg)

        rc = C.zmq_msg_recv(zmq_msg, self._zmq_socket, flags)

        if rc < 0:
            C.zmq_msg_close(zmq_msg)
            _check_rc(rc)

        value = ffi.buffer(C.zmq_msg_data(zmq_msg), C.zmq_msg_size(zmq_msg))[:]

        frame = Frame(value, track=track)
        frame.more = self.getsockopt(RCVMORE)
        if copy:
            return frame.bytes
        else:
            return frame
            

__all__ = ['Socket', 'IPC_PATH_MAX_LEN']
