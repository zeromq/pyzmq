# coding: utf-8
"""miscellaneous zmq_utils wrapping"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013-2014 Felipe Cruz, Min Ragan-Kelley, Pawel Jasinski
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from ._iron_ctypes import libzmq
from ctypes import create_string_buffer

from zmq.error import ZMQError, _check_rc

def curve_keypair():
    """generate a Z85 keypair for use with zmq.CURVE security
    
    Requires libzmq (>= 4.0) to have been linked with libsodium.
    
    Returns
    -------
    (public, secret) : two bytestrings
        The public and private keypair as 40 byte z85-encoded bytestrings.
    """
    public = create_string_buffer(64)
    private = create_string_buffer(64)
    rc = libzmq.zmq_curve_keypair(public, private)
    _check_rc(rc)
    return public[:40], private[:40]


class Stopwatch(object):
    def __init__(self):
        self.watch = None

    def start(self):
        if self.watch == None:
            self.watch = libzmq.zmq_stopwatch_start()
        else:
            raise ZMQError('Stopwatch is already runing.')

    def stop(self):
        if self.watch == None:
            raise ZMQError('Must start the Stopwatch before calling stop.')
        else:
            time = libzmq.zmq_stopwatch_stop(self.watch)
            if isinstance(time, int):
                time = long(time)
            self.watch = None
            return time

    # staticmethod?
    def sleep(self, seconds):
        libzmq.zmq_sleep(seconds)

__all__ = ['curve_keypair', 'Stopwatch']
