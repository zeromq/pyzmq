# coding: utf-8
"""zmq device functions"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from ._cffi import C, ffi, zmq_version_info
from .socket import Socket
from zmq.error import ZMQError, _check_rc

def device(device_type, frontend, backend):
    rc = C.zmq_proxy(frontend._zmq_socket, backend._zmq_socket, ffi.NULL)
    _check_rc(rc)

def proxy(frontend, backend, capture=None):
    if isinstance(capture, Socket):
        capture = capture._zmq_socket
    else:
        capture = ffi.NULL

    rc = C.zmq_proxy(frontend._zmq_socket, backend._zmq_socket, capture)
    _check_rc(rc)

__all__ = ['device', 'proxy']
