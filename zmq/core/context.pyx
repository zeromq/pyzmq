"""0MQ Context class."""

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

from czmq cimport *
from socket cimport Socket
# 
from error import ZMQError
from constants import *

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


cdef class Context:
    """Context(io_threads=1)

    Manage the lifecycle of a 0MQ context.

    This class no longer takes any flags or the number of application
    threads.

    Parameters
    ----------
    io_threads : int
        The number of IO threads.
    """
    
    def __cinit__(self, int io_threads=1):
        self.handle = NULL
        if not io_threads > 0:
            raise ZMQError(EINVAL)
        with nogil:
            self.handle = zmq_init(io_threads)
        if self.handle == NULL:
            raise ZMQError()
        self.closed = False

    def __dealloc__(self):
        cdef int rc
        if self.handle != NULL:
            with nogil:
                rc = zmq_term(self.handle)
            if rc != 0:
                raise ZMQError()

    def term(self):
        """ctx.term()

        Close or terminate the context.

        This can be called to close the context by hand. If this is not
        called, the context will automatically be closed when it is
        garbage collected.
        """
        cdef int rc
        if self.handle != NULL and not self.closed:
            with nogil:
                rc = zmq_term(self.handle)
            if rc != 0:
                raise ZMQError()
            self.handle = NULL
            self.closed = True

    def socket(self, int socket_type):
        """ctx.socket(socket_type)

        Create a Socket associated with this Context.

        Parameters
        ----------
        socket_type : int
            The socket type, which can be any of the 0MQ socket types: 
            REQ, REP, PUB, SUB, PAIR, XREQ, XREP, PULL, PUSH, XSUB, XPUB.
        """
        if self.closed:
            raise ZMQError(ENOTSUP)
        return Socket(self, socket_type)

    @property
    def _handle(self):
        return <Py_ssize_t> self.handle

__all__ = ['Context']
