"""Python bindings for 0MQ."""

#
#    Copyright (c) 2010 Brian E. Granger
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

from czmq cimport zmq_strerror, zmq_errno

def strerror(errnum):
    """Return the error string given the error number."""
    return zmq_strerror(errnum)


class ZMQBaseError(Exception):
    pass


class ZMQError(ZMQBaseError):
    """Base exception class for 0MQ errors in Python."""

    def __init__(self, error=None):
        """Wrap an errno style error.

        Parameters
        ----------
        error : int
            The ZMQ errno or None.  If None, then zmq_errno() is called and
            used.
        """
        if error is None:
            error = zmq_errno()
        if type(error) == int:
            self.strerror = strerror(error)
            self.errno = error
        else:
            self.strerror = str(error)
            self.errno = None

    def __str__(self):
        return self.strerror


class ZMQBindError(ZMQBaseError):
    """An error for bind_to_random_port."""
    pass


class NotDone(ZMQBaseError):
    """For raising in MessageTracker.wait"""
    pass
