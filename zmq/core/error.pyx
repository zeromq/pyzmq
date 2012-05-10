"""0MQ Error classes and functions."""

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

# allow const char*
cdef extern from *:
    ctypedef char* const_char_ptr "const char*"

from cpython cimport PyErr_CheckSignals

from libzmq cimport zmq_strerror, zmq_errno

from zmq.utils.strtypes import bytes

def strerror(int errnum):
    """strerror(errnum)

    Return the error string given the error number.
    """
    cdef const_char_ptr str_e
    # char * will be a bytes object:
    with nogil:
        str_e = zmq_strerror(errnum)
    if str is bytes:
        # Python 2: str is bytes, so we already have the right type
        return str_e
    else:
        # Python 3: decode bytes to unicode str
        return str_e.decode()


class ZMQBaseError(Exception):
    """Base exception class for 0MQ errors in Python."""
    pass


class ZMQError(ZMQBaseError):
    """Wrap an errno style error.

    Parameters
    ----------
    error : int
        The ZMQ errno or None.  If None, then ``zmq_errno()`` is called and
        used.
    msg : string
        Description of the error or None.
    """

    def __init__(self, error=None, msg=None):
        """Wrap an errno style error.

        Parameters
        ----------
        error : int
            The ZMQ errno or None.  If None, then ``zmq_errno()`` is called and
            used.
        msg : string
            Description of the error or None.
        """
        cdef int errno
        if error is None:
            with nogil:
                errno = zmq_errno()
            error = errno
        if type(error) == int:
            self.errno = error
            if msg is None:
                self.strerror = strerror(error)
            else:
                self.strerror = msg
        else:
            self.errno = None
            if msg is None:
                self.strerror = str(error)
            else:
                self.strerror = msg
        # flush signals, because there could be a SIGINT
        # waiting to pounce, resulting in uncaught exceptions.
        # Doing this here means getting SIGINT during a blocking
        # libzmq call will raise a *catchable* KeyboardInterrupt
        PyErr_CheckSignals()

    def __str__(self):
        return self.strerror
    
    def __repr__(self):
        return "ZMQError('%s')"%self.strerror


class ZMQBindError(ZMQBaseError):
    """An error for ``Socket.bind_to_random_port()``.
    
    See Also
    --------
    .Socket.bind_to_random_port
    """
    pass


class NotDone(ZMQBaseError):
    """Raised when timeout is reached while waiting for 0MQ to finish with a Message
    
    See Also
    --------
    .MessageTracker.wait : object for tracking when ZeroMQ is done
    """
    pass


__all__ = ['strerror', 'ZMQBaseError', 'ZMQBindError', 'ZMQError', 'NotDone']
