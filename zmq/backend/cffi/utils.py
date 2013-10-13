# coding: utf-8
"""miscellaneous zmq_utils wrapping"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from ._cffi import ffi, C

from zmq.error import ZMQError, _check_rc

def curve_keypair():
    """generate a Z85 keypair for use with zmq.CURVE security
    
    Requires libzmq (≥ 4.0) to have been linked with libsodium.
    
    Returns
    -------
    (public, secret) : two bytestrings
        The public and private keypair as 40 byte z85-encoded bytestrings.
    """
    public = ffi.new('char[64]')
    private = ffi.new('char[64]')
    rc = C.zmq_curve_keypair(public, private)
    _check_rc(rc)
    return ffi.buffer(public)[:40], ffi.buffer(private)[:40]


class Stopwatch(object):
    def __init__(self):
        self.watch = ffi.NULL

    def start(self):
        if self.watch == ffi.NULL:
            self.watch = C.zmq_stopwatch_start()
        else:
            raise ZMQError('Stopwatch is already runing.')

    def stop(self):
        if self.watch == ffi.NULL:
            raise ZMQError('Must start the Stopwatch before calling stop.')
        else:
            time = C.zmq_stopwatch_stop(self.watch)
            self.watch = ffi.NULL
            return time

    def sleep(self, seconds):
        C.zmq_sleep(seconds)

__all__ = ['curve_keypair', 'Stopwatch']
