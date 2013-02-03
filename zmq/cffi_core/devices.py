# coding: utf-8

from ._cffi import C, ffi, zmq_version_info
from .socket import Socket
from zmq.error import ZMQError

def device(device_type, frontend, backend):
    return C.zmq_proxy(frontend._zmq_socket, backend._zmq_socket, ffi.NULL)

def proxy(frontend, backend, capture=None):
    if isinstance(capture, Socket):
        capture = capture._zmq_socket
    else:
        capture = ffi.NULL

    rc = C.zmq_proxy(frontend._zmq_socket, backend._zmq_socket, capture)
    _check_rc(rc)

__all__ = ['device', 'proxy']
