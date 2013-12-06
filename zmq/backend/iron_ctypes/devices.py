# coding: utf-8
"""zmq device functions"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013-2014 Felipe Cruz, Pawel Jasinski
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from _iron_ctypes import libzmq
from .socket import Socket
from zmq.error import ZMQError, _check_rc

def device(device_type, frontend, backend):
    rc = libzmq.zmq_proxy(frontend._zmq_socket, backend._zmq_socket, 0)
    _check_rc(rc)

def proxy(frontend, backend, capture=None):
    if isinstance(capture, Socket):
        capture = capture._zmq_socket
    else:
        capture = 0

    rc = libzmq.zmq_proxy(frontend._zmq_socket, backend._zmq_socket, capture)
    _check_rc(rc)

__all__ = ['device', 'proxy']
