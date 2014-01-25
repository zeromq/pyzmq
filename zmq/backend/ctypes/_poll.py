# coding: utf-8
"""zmq poll function"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz, Pawel Jasinski
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import ctypes
from System import Int64

from ._ctypes import libzmq, zmq_pollitem_t
from .constants import *
from zmq.error import _check_rc

import zmq

def _make_zmq_pollitem(socket, flags):
    zmq_pollitem = zmq_pollitem_t()
    zmq_socket = socket._zmq_socket
    zmq_pollitem.socket = zmq_socket
    zmq_pollitem.fd = 0
    zmq_pollitem.events = flags
    zmq_pollitem.revents = 0
    return zmq_pollitem

def _make_zmq_pollitem_fromfd(socket_fd, flags):
    zmq_pollitem = zmq_pollitem_t()
    zmq_pollitem.socket = 0
    zmq_pollitem.fd = socket_fd
    zmq_pollitem.events = flags
    zmq_pollitem.revents = 0
    return zmq_pollitem

def zmq_poll(sockets, timeout):
    low_level_to_socket_obj = {}
    size = len(sockets)
    items = (zmq_pollitem_t * size)()
    for idx, item in enumerate(sockets):
        if isinstance(item[0], int):
            low_level_to_socket_obj[item[0]] = item
            items[idx] = _make_zmq_pollitem_fromfd(item[0], item[1])
        elif isinstance(item[0], Int64):
            low_level_to_socket_obj[item[0]] = item
            items[idx] = _make_zmq_pollitem_fromfd(item[0], item[1])
        elif isinstance(item[0], zmq.Socket):
            low_level_to_socket_obj[item[0]._zmq_socket] = item
            items[idx] = _make_zmq_pollitem(item[0], item[1])
        elif hasattr(item[0], 'fileno'):
            items[idx] = _make_zmq_pollitem_fromfd(item[0].fileno(), item[1])
        else:
            raise TypeError("unable to obtain file descriptor at: %d type: %s" % (idx, type(item[0])))

    list_length = ctypes.c_int(size)
    c_timeout = ctypes.c_long(timeout)
    rc = libzmq.zmq_poll(ctypes.cast(items, ctypes.POINTER(zmq_pollitem_t)), list_length, c_timeout)
    _check_rc(rc)
    result = []
    for index in range(len(items)):
        if not items[index].socket == 0:
            if items[index].revents > 0:
                result.append((low_level_to_socket_obj[items[index].socket][0],
                            items[index].revents))
        else:
            result.append((items[index].fd, items[index].revents))
    return result

__all__ = ['zmq_poll']
