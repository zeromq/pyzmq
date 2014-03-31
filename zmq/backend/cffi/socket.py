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
                    IPC_PATH_MAX_LEN)

from .message import Frame
from .constants import *

import zmq
from zmq.error import ZMQError, _check_rc, _check_version
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
        raise ZMQError(zmq.EINVAL)

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
        raise ZMQError(zmq.EINVAL)

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
        raise ZMQError(zmq.EINVAL)


class Socket(object):
    context = None
    socket_type = None
    _zmq_socket = None
    _closed = None
    _ref = None
    _shadow = False

    def __init__(self, context=None, socket_type=None, shadow=None):
        self.context = context
        if shadow is not None:
            self._zmq_socket = ffi.cast("void *", shadow)
            self._shadow = True
        else:
            self._shadow = False
            self._zmq_socket = C.zmq_socket(context._zmq_ctx, socket_type)
        if self._zmq_socket == ffi.NULL:
            raise ZMQError()
        self._closed = False
        if context:
            self._ref = context._add_socket(self)
    
    @property
    def underlying(self):
        """The address of the underlying libzmq socket"""
        return int(ffi.cast('size_t', self._zmq_socket))
    
    @property
    def closed(self):
        return self._closed

    def close(self, linger=None):
        rc = 0
        if not self._closed and hasattr(self, '_zmq_socket'):
            if self._zmq_socket is not None:
                rc = C.zmq_close(self._zmq_socket)
            self._closed = True
            if self.context:
                self.context._rm_socket(self._ref)
        return rc

    def __del__(self):
        if not self._shadow:
            self.close()

    def bind(self, address):
        if isinstance(address, unicode):
            address = address.encode('utf8')
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
        _check_version((3,2), "unbind")
        if isinstance(address, unicode):
            address = address.encode('utf8')
        rc = C.zmq_unbind(self._zmq_socket, address)
        _check_rc(rc)

    def connect(self, address):
        if isinstance(address, unicode):
            address = address.encode('utf8')
        rc = C.zmq_connect(self._zmq_socket, address)
        _check_rc(rc)

    def disconnect(self, address):
        _check_version((3,2), "disconnect")
        if isinstance(address, unicode):
            address = address.encode('utf8')
        rc = C.zmq_disconnect(self._zmq_socket, address)
        _check_rc(rc)

    def set(self, option, value):
        length = None
        if isinstance(value, unicode):
            raise TypeError("unicode not allowed, use bytes")
        
        if isinstance(value, bytes):
            if option not in zmq.constants.bytes_sockopts:
                raise TypeError("not a bytes sockopt: %s" % option)
            length = len(value)
        
        c_data = initialize_opt_pointer(option, value, length)

        c_value_pointer = c_data[0]
        c_sizet = c_data[1]

        rc = C.zmq_setsockopt(self._zmq_socket,
                               option,
                               ffi.cast('void*', c_value_pointer),
                               c_sizet)
        _check_rc(rc)

    def get(self, option):
        c_data = new_pointer_from_opt(option, length=255)

        c_value_pointer = c_data[0]
        c_sizet_pointer = c_data[1]

        rc = C.zmq_getsockopt(self._zmq_socket,
                               option,
                               c_value_pointer,
                               c_sizet_pointer)
        _check_rc(rc)
        
        sz = c_sizet_pointer[0]
        v = value_from_opt_pointer(option, c_value_pointer, sz)
        if option != zmq.IDENTITY and option in zmq.constants.bytes_sockopts and v.endswith(b'\0'):
            v = v[:-1]
        return v

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

        _buffer = ffi.buffer(C.zmq_msg_data(zmq_msg), C.zmq_msg_size(zmq_msg))
        value = _buffer[:]
        C.zmq_msg_close(zmq_msg)

        frame = Frame(value, track=track)
        frame.more = self.getsockopt(RCVMORE)

        if copy:
            return frame.bytes
        else:
            return frame
    
    def monitor(self, addr, events=-1):
        """s.monitor(addr, flags)

        Start publishing socket events on inproc.
        See libzmq docs for zmq_monitor for details.
        
        Note: requires libzmq >= 3.2
        
        Parameters
        ----------
        addr : str
            The inproc url used for monitoring.
        events : int [default: zmq.EVENT_ALL]
            The zmq event bitmask for which events will be sent to the monitor.
        """
        
        _check_version((3,2), "monitor")
        if events < 0:
            events = zmq.EVENT_ALL
        rc = C.zmq_socket_monitor(self._zmq_socket, addr, events)


__all__ = ['Socket', 'IPC_PATH_MAX_LEN']
