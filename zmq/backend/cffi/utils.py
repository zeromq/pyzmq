# coding: utf-8
"""miscellaneous zmq_utils wrapping"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from errno import EINTR

from ._cffi import ffi, C

from zmq.error import ZMQError, InterruptedSystemCall, _check_rc, _check_version
from zmq.utils.strtypes import unicode


def has(capability):
    """Check for zmq capability by name (e.g. 'ipc', 'curve')
    
    .. versionadded:: libzmq-4.1
    .. versionadded:: 14.1
    """
    _check_version((4,1), 'zmq.has')
    if isinstance(capability, unicode):
        capability = capability.encode('utf8')
    return bool(C.zmq_has(capability))


def curve_keypair():
    """generate a Z85 keypair for use with zmq.CURVE security
    
    Requires libzmq (≥ 4.0) to have been built with CURVE support.
    
    Returns
    -------
    (public, secret) : two bytestrings
        The public and private keypair as 40 byte z85-encoded bytestrings.
    """
    _check_version((3,2), "monitor")
    public = ffi.new('char[64]')
    private = ffi.new('char[64]')
    rc = C.zmq_curve_keypair(public, private)
    _check_rc(rc)
    return ffi.buffer(public)[:40], ffi.buffer(private)[:40]


def _retry_sys_call(f, *args, **kwargs):
    """make a call, retrying if interrupted with EINTR"""
    while True:
        rc = f(*args)
        try:
            _check_rc(rc)
        except InterruptedSystemCall:
            continue
        else:
            break


__all__ = ['has', 'curve_keypair']
