"""0MQ Context class."""

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

from libc.stdlib cimport free, malloc, realloc
from errno import ENOTSOCK

from libzmq cimport *

from error import ZMQError
from constants import *

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

_instance = None

cdef class Context:
    """Context(io_threads=1)

    Manage the lifecycle of a 0MQ context.

    Parameters
    ----------
    io_threads : int
        The number of IO threads.
    """
    
    def __cinit__(self, int io_threads=1):
        self.handle = NULL
        self._sockets = NULL
        if not io_threads > 0:
            raise ZMQError(EINVAL)
        with nogil:
            self.handle = zmq_init(io_threads)
        if self.handle == NULL:
            raise ZMQError()
        self.closed = False
        self.n_sockets = 0
        self.max_sockets = 32
        
        self._sockets = <void **>malloc(self.max_sockets*sizeof(void *))
        if self._sockets == NULL:
            raise MemoryError("Could not allocate _sockets array")
        

    def __dealloc__(self):
        cdef int rc
        if self.handle != NULL:
            self.term()
        if self._sockets != NULL:
            free(self._sockets)
    
    cdef inline void _add_socket(self, void* handle):
        """Add a socket handle to be closed when Context terminates.
        
        This is to be called in the Socket constructor.
        """
        # print self.n_sockets, self.max_sockets
        if self.n_sockets >= self.max_sockets:
            self.max_sockets *= 2
            self._sockets = <void **>realloc(self._sockets, self.max_sockets*sizeof(void *))
            if self._sockets == NULL:
                raise MemoryError("Could not reallocate _sockets array")
        
        self._sockets[self.n_sockets] = handle
        self.n_sockets += 1
        # print self.n_sockets, self.max_sockets

    cdef inline void _remove_socket(self, void* handle):
        """Remove a socket from the collected handles.
        
        This should be called by Socket.close, to prevent trying to
        close a socket a second time.
        """
        cdef bint found = False
        
        for idx in range(self.n_sockets):
            if self._sockets[idx] == handle:
                found=True
                break
        
        if found:
            self.n_sockets -= 1
            if self.n_sockets:
                # move last handle to closed socket's index
                self._sockets[idx] = self._sockets[self.n_sockets]
    
    # instance method copied from tornado IOLoop.instance
    @classmethod
    def instance(cls, int io_threads=1):
        """Returns a global Context instance.

        Most single-threaded applications have a single, global Context.
        Use this method instead of passing around Context instances
        throughout your code.

        A common pattern for classes that depend on Contexts is to use
        a default argument to enable programs with multiple Contexts
        but not require the argument for simpler applications:

            class MyClass(object):
                def __init__(self, context=None):
                    self.context = context or Context.instance()
        """
        global _instance
        if _instance is None or _instance.closed:
            _instance = cls(io_threads)
        return _instance

    def term(self):
        """ctx.term()

        Close or terminate the context and all its sockets.

        This can be called to close the context by hand. If this is not
        called, the context will automatically be closed when it is
        garbage collected.
        """
        cdef int rc
        cdef int i=-1
        if self.handle != NULL and not self.closed:
            for i in range(self.n_sockets):
                # print 'closing: ', <size_t>self._sockets[i]
                with nogil:
                    rc = zmq_close(self._sockets[i])
                if rc != 0 and zmq_errno() != ENOTSOCK:
                    raise ZMQError()
            # print i
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
            REQ, REP, PUB, SUB, PAIR, XREQ, DEALER, XREP, ROUTER, PULL, PUSH, XSUB, XPUB.
        """
        # import here to prevent circular import
        from zmq.core.socket import Socket
        if self.closed:
            raise ZMQError(ENOTSUP)
        return Socket(self, socket_type)

    @property
    def _handle(self):
        return <Py_ssize_t> self.handle

__all__ = ['Context']
