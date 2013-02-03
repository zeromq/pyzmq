# coding: utf-8
"""zmq Stopwatch class"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from zmq.cffi_core._cffi import ffi, C

from zmq.error import ZMQError

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

__all__ = ['Stopwatch']

