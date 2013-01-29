# coding: utf-8

from ._cffi import C, ffi, zmq_version_info
from .socket import Socket
from zmq.error import ZMQError

def device(device_type, isocket, osocket):
    rc = C.zmq_device(device_type, isocket.zmq_socket, osocket.zmq_socket)

    if rc != 0:
        raise ZMQError(C.zmq_errno())

    return rc

def proxy(isocket, osocket, msocket=None):
    if isinstance(msocket, Socket):
        msocket = msocket.zmq_socket
    else:
        msocket = ffi.NULL

    rc = C.zmq_proxy(isocket.zmq_socket, osocket.zmq_socket, msocket)

    if rc != 0:
        raise ZMQError(C.zmq_errno())

    return rc

__all__ = ['device', 'proxy']
