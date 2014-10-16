"""0MQ utils."""

#
#    Copyright (c) 2010-2011 Brian E. Granger & Min Ragan-Kelley
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from libzmq cimport (
    zmq_stopwatch_start, zmq_stopwatch_stop, zmq_sleep, zmq_curve_keypair,
    zmq_has, const_char_ptr
)
from zmq.error import ZMQError, _check_rc, _check_version
from zmq.utils.strtypes import unicode

def has(capability):
    """Check for zmq capability by name (e.g. 'ipc', 'curve')
    
    .. versionadded:: libzmq-4.1
    .. versionadded:: 14.1
    """
    _check_version((4,1), 'zmq.has')
    cdef bytes ccap
    if isinstance(capability, unicode):
        capability = capability.encode('utf8')
    ccap = capability
    return bool(zmq_has(ccap))

def curve_keypair():
    """generate a Z85 keypair for use with zmq.CURVE security
    
    Requires libzmq (≥ 4.0) to have been linked with libsodium.
    
    .. versionadded:: libzmq-4.0
    .. versionadded:: 14.0
    
    Returns
    -------
    (public, secret) : two bytestrings
        The public and private keypair as 40 byte z85-encoded bytestrings.
    """
    cdef int rc
    cdef char[64] public_key
    cdef char[64] secret_key
    _check_version((4,0), "curve_keypair")
    rc = zmq_curve_keypair (public_key, secret_key)
    _check_rc(rc)
    return public_key, secret_key


cdef class Stopwatch:
    """Stopwatch()

    A simple stopwatch based on zmq_stopwatch_start/stop.

    This class should be used for benchmarking and timing 0MQ code.
    """

    def __cinit__(self):
        self.watch = NULL

    def __dealloc__(self):
        # copy of self.stop() we can't call object methods in dealloc as it
        # might already be partially deleted
        if self.watch:
            zmq_stopwatch_stop(self.watch)
            self.watch = NULL

    def start(self):
        """s.start()

        Start the stopwatch.
        """
        if self.watch == NULL:
            self.watch = zmq_stopwatch_start()
        else:
            raise ZMQError('Stopwatch is already running.')

    def stop(self):
        """s.stop()

        Stop the stopwatch.
        
        Returns
        -------
        t : unsigned long int
            the number of microseconds since ``start()`` was called.
        """
        cdef unsigned long time
        if self.watch == NULL:
            raise ZMQError('Must start the Stopwatch before calling stop.')
        else:
            time = zmq_stopwatch_stop(self.watch)
            self.watch = NULL
            return time

    def sleep(self, int seconds):
        """s.sleep(seconds)

        Sleep for an integer number of seconds.
        """
        with nogil:
            zmq_sleep(seconds)


__all__ = ['has', 'curve_keypair', 'Stopwatch']
