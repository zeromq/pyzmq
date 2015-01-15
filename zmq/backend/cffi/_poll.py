# coding: utf-8
"""zmq poll function"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from ._cffi import C, ffi, zmq_version_info

from .constants import *

from zmq.error import _check_rc


def _make_zmq_pollitem(socket, flags):
    zmq_socket = socket._zmq_socket
    zmq_pollitem = ffi.new('zmq_pollitem_t*')
    zmq_pollitem.socket = zmq_socket
    zmq_pollitem.fd = 0
    zmq_pollitem.events = flags
    zmq_pollitem.revents = 0
    return zmq_pollitem[0]

def _make_zmq_pollitem_fromfd(socket_fd, flags):
    zmq_pollitem = ffi.new('zmq_pollitem_t*')
    zmq_pollitem.socket = ffi.NULL
    zmq_pollitem.fd = socket_fd
    zmq_pollitem.events = flags
    zmq_pollitem.revents = 0
    return zmq_pollitem[0]

def zmq_poll(sockets, timeout):
    cffi_pollitem_list = []
    low_level_to_socket_obj = {}
    for item in sockets:
        if isinstance(item[0], int):
            low_level_to_socket_obj[item[0]] = item
            cffi_pollitem_list.append(_make_zmq_pollitem_fromfd(item[0], item[1]))
        else:
            low_level_to_socket_obj[item[0]._zmq_socket] = item
            cffi_pollitem_list.append(_make_zmq_pollitem(item[0], item[1]))
    items = ffi.new('zmq_pollitem_t[]', cffi_pollitem_list)
    list_length = ffi.cast('int', len(cffi_pollitem_list))
    c_timeout = ffi.cast('long', timeout)
    rc = C.zmq_poll(items, list_length, c_timeout)
    _check_rc(rc)
    result = []
    for index in range(len(items)):
        if not items[index].socket == ffi.NULL:
            if items[index].revents > 0:
                result.append((low_level_to_socket_obj[items[index].socket][0],
                            items[index].revents))
        else:
            result.append((items[index].fd, items[index].revents))
    return result

__all__ = ['zmq_poll']
