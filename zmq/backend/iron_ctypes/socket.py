# coding: utf-8
"""zmq Socket class"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013-2014 Felipe Cruz, Pawel Jasinski
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import random
import codecs
import ctypes

import errno as errno_mod

from .message import Frame
from .constants import *
from ._iron_ctypes import libzmq, zmq_msg_t, EMPTY_STRING

import zmq
from zmq.error import ZMQError, _check_rc
from zmq.utils.strtypes import unicode


class Socket(object):
    context = None
    socket_type = None
    _zmq_socket = None
    _closed = None
    _ref = None

    def __init__(self, context, sock_type):
        self.context = context
        self.socket_type = sock_type
        self._zmq_socket = libzmq.zmq_socket(context._zmq_ctx, sock_type)
        if self._zmq_socket == 0:
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
                rc = libzmq.zmq_close(self._zmq_socket)
            self._closed = True
            self.context._rm_socket(self._ref)
        return rc

    def __del__(self):
        self.close()

    def bind(self, address):
        if len(address) == 0:
            address = EMPTY_STRING
        rc = libzmq.zmq_bind(self._zmq_socket, address)
        if rc < 0:
            if IPC_PATH_MAX_LEN and libzmq.zmq_errno() == errno_mod.ENAMETOOLONG:
                # py3compat: address is bytes, but msg wants str
                if str is unicode:
                    address = address.decode('utf-8', 'replace')
                path = address.split('://', 1)[-1]
                msg = ('ipc path "{0}" is longer than {1} '
                                'characters (sizeof(sockaddr_un.sun_path)).'
                                .format(path, IPC_PATH_MAX_LEN))
                raise ZMQError(libzmq.zmq_errno(), msg=msg)
            else:
                _check_rc(rc)

    def unbind(self, address):
        rc = libzmq.zmq_unbind(self._zmq_socket, address)
        _check_rc(rc)

    def connect(self, address):
        if len(address) == 0:
            address = EMPTY_STRING
        rc = libzmq.zmq_connect(self._zmq_socket, address)
        _check_rc(rc)

    def disconnect(self, address):
        rc = libzmq.zmq_disconnect(self._zmq_socket, address)
        _check_rc(rc)

    def set(self, option, value):
        if isinstance(value, unicode):
            raise TypeError("unicode not allowed, use bytes")
        
        if isinstance(value, bytes):
            if option not in zmq.constants.bytes_sockopts:
                raise TypeError("not a bytes sockopt: %s" % option)

        if option in zmq.constants.int64_sockopts:
            value = ctypes.c_longlong(value)
            size = ctypes.sizeof(value)
        elif option in zmq.constants.int_sockopts:
            value = ctypes.c_long(value)
            size = ctypes.sizeof(value)
        elif option in zmq.constants.bytes_sockopts:
            size = len(value)
            buf = ctypes.create_string_buffer(size)
            if size != 0:
                ctypes.memmove(ctypes.addressof(buf), value, size)
            value = buf
        else:
            raise ZMQError(EINVAL)
        
        rc = libzmq.zmq_setsockopt(self._zmq_socket, option, ctypes.byref(value), size) 
        _check_rc(rc)

    def get(self, option):
        if option in zmq.constants.int64_sockopts:
            value = ctypes.c_longlong()
        elif option in zmq.constants.int_sockopts:
            value = ctypes.c_long()
        elif option in zmq.constants.bytes_sockopts:
            value = ctypes.create_string_buffer(255)
        else:
            raise ZMQError(EINVAL)
        size = ctypes.c_size_t(ctypes.sizeof(value))
        rc = libzmq.zmq_getsockopt(self._zmq_socket, option, ctypes.byref(value), ctypes.byref(size))
        _check_rc(rc)
       
        if option in zmq.constants.bytes_sockopts:
            v = bytes(size.value)
            ctypes.memmove(v, value, size)
        else:
            v = value.value
        if option != zmq.IDENTITY and option in zmq.constants.bytes_sockopts and v.endswith(b'\0'):
            v = v[:-1]
        return v

    def send(self, message, flags=0, copy=False, track=False):
        if isinstance(message, unicode):
            raise TypeError("Message must be in bytes, not an unicode Object")

        if isinstance(message, Frame):
            message = message.bytes

        flags = ctypes.c_int(flags)
        zmq_msg = zmq_msg_t()
        msg_c_len = len(message)
        rc = libzmq.zmq_msg_init_size(zmq_msg, msg_c_len)
        _check_rc(rc)

        msg_buf = libzmq.zmq_msg_data(zmq_msg)
        msg_buf_size = libzmq.zmq_msg_size(zmq_msg)
        if len(message) != 0:
            ctypes.memmove(msg_buf, message, msg_buf_size)

        rc = libzmq.zmq_msg_send(zmq_msg, self._zmq_socket, flags)
        libzmq.zmq_msg_close(zmq_msg)
        _check_rc(rc)

        if track:
            return zmq.MessageTracker()

    def recv(self, flags=0, copy=True, track=False):
        zmq_msg = zmq_msg_t()
        libzmq.zmq_msg_init(zmq_msg)
        flags = ctypes.c_int(flags)

        rc = libzmq.zmq_msg_recv(zmq_msg, self._zmq_socket, flags)

        if rc < 0:
            libzmq.zmq_msg_close(zmq_msg)
            _check_rc(rc)
        
        data = libzmq.zmq_msg_data(zmq_msg)
        size = libzmq.zmq_msg_size(zmq_msg)

        ret = bytes(size)
        if size != 0:
            ctypes.memmove(ret, data, size)

        libzmq.zmq_msg_close(zmq_msg)

        frame = Frame(ret, track=track)
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
        if zmq.zmq_version_info() < (3,2):
            raise NotImplementedError("monitor requires libzmq >= 3.2, have %s" % zmq.zmq_version())
        if events < 0:
            events = zmq.EVENT_ALL
        rc = libzmq.zmq_socket_monitor(self._zmq_socket, addr, events)
        _check_rc(rc)

IPC_PATH_MAX_LEN = 1024 # this is not supported under window, how about mono?
__all__ = ['Socket', 'IPC_PATH_MAX_LEN']
