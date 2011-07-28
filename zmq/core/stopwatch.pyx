"""0MQ Stopwatch class."""

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

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from libzmq cimport zmq_stopwatch_start, zmq_stopwatch_stop, zmq_sleep

from zmq.core.error import ZMQError

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

cdef class Stopwatch:
    """Stopwatch()

    A simple stopwatch based on zmq_stopwatch_start/stop.

    This class should be used for benchmarking and timing 0MQ code.
    """

    def __cinit__(self):
        self.watch = NULL

    def __dealloc__(self):
        try:
            self.stop()
        except ZMQError:
            pass

    def start(self):
        """s.start()

        Start the stopwatch.
        """
        if self.watch == NULL:
            with nogil:
                self.watch = zmq_stopwatch_start()
        else:
            raise ZMQError('Stopwatch is already runing.')

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
            with nogil:
                time = zmq_stopwatch_stop(self.watch)
            self.watch = NULL
            return time

    def sleep(self, int seconds):
        """s.sleep(seconds)

        Sleep for an integer number of seconds.
        """
        with nogil:
            zmq_sleep(seconds)


__all__ = ['Stopwatch']
