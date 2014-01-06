"""0MQ Context class."""
# coding: utf-8

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

from libzmq cimport *

cdef extern from "getpid_compat.h":
    int getpid()

from zmq.error import ZMQError
from zmq.backend.cython.checkrc cimport _check_rc

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
    
    def __cinit__(self, int io_threads = 1, **kwargs):
        self.handle = NULL
        self._sockets = NULL
        
        if ZMQ_VERSION_MAJOR >= 3:
            self.handle = zmq_ctx_new()
        else:
            self.handle = zmq_init(io_threads)
        
        if self.handle == NULL:
            raise ZMQError()
        
        cdef int rc = 0
        if ZMQ_VERSION_MAJOR >= 3:
            rc = zmq_ctx_set(self.handle, ZMQ_IO_THREADS, io_threads)
            _check_rc(rc)
        
        self.closed = False
        self._n_sockets = 0
        self._max_sockets = 32
        
        self._sockets = <void **>malloc(self._max_sockets*sizeof(void *))
        if self._sockets == NULL:
            raise MemoryError("Could not allocate _sockets array")
        
        self._pid = getpid()
    
    def __init__(self, io_threads=1):
        # no-op
        pass
    

    def __del__(self):
        """deleting a Context should terminate it, without trying non-threadsafe destroy"""
        self.term()
    
    def __dealloc__(self):
        """don't touch members in dealloc, just cleanup allocations"""
        cdef int rc
        if self._sockets != NULL:
            free(self._sockets)
            self._sockets = NULL
            self._n_sockets = 0

        # we can't call object methods in dealloc as it
        # might already be partially deleted
        self._term()
    
    cdef inline void _add_socket(self, void* handle):
        """Add a socket handle to be closed when Context terminates.
        
        This is to be called in the Socket constructor.
        """
        # print self._n_sockets, self._max_sockets
        if self._n_sockets >= self._max_sockets:
            self._max_sockets *= 2
            self._sockets = <void **>realloc(self._sockets, self._max_sockets*sizeof(void *))
            if self._sockets == NULL:
                raise MemoryError("Could not reallocate _sockets array")
        
        self._sockets[self._n_sockets] = handle
        self._n_sockets += 1
        # print self._n_sockets, self._max_sockets

    cdef inline void _remove_socket(self, void* handle):
        """Remove a socket from the collected handles.
        
        This should be called by Socket.close, to prevent trying to
        close a socket a second time.
        """
        cdef bint found = False
        
        for idx in range(self._n_sockets):
            if self._sockets[idx] == handle:
                found=True
                break
        
        if found:
            self._n_sockets -= 1
            if self._n_sockets:
                # move last handle to closed socket's index
                self._sockets[idx] = self._sockets[self._n_sockets]
    
    @property
    def _handle(self):
        return <Py_ssize_t> self.handle
    
    cdef inline int _term(self):
        cdef int rc=0
        if self.handle != NULL and not self.closed and getpid() == self._pid:
            with nogil:
                rc = zmq_ctx_destroy(self.handle)
        self.handle = NULL
        return rc
    
    def term(self):
        """ctx.term()

        Close or terminate the context.
        
        This can be called to close the context by hand. If this is not called,
        the context will automatically be closed when it is garbage collected.
        """
        cdef int rc
        rc = self._term()
        self.closed = True
    
    def set(self, int option, optval):
        """ctx.set(option, optval)

        Set a context option.

        See the 0MQ API documentation for zmq_ctx_set
        for details on specific options.
        
        .. versionadded:: libzmq-3.2
        .. versionadded:: 13.0

        Parameters
        ----------
        option : int
            The option to set.  Available values will depend on your
            version of libzmq.  Examples include::
            
                zmq.IO_THREADS, zmq.MAX_SOCKETS
        
        optval : int
            The value of the option to set.
        """
        cdef int optval_int_c
        cdef int rc
        cdef char* optval_c

        if self.closed:
            raise RuntimeError("Context has been destroyed")
        
        if not isinstance(optval, int):
            raise TypeError('expected int, got: %r' % optval)
        optval_int_c = optval
        rc = zmq_ctx_set(self.handle, option, optval_int_c)
        _check_rc(rc)

    def get(self, int option):
        """ctx.get(option)

        Get the value of a context option.

        See the 0MQ API documentation for zmq_ctx_get
        for details on specific options.
        
        .. versionadded:: libzmq-3.2
        .. versionadded:: 13.0

        Parameters
        ----------
        option : int
            The option to get.  Available values will depend on your
            version of libzmq.  Examples include::
            
                zmq.IO_THREADS, zmq.MAX_SOCKETS
            
        Returns
        -------
        optval : int
            The value of the option as an integer.
        """
        cdef int optval_int_c
        cdef size_t sz
        cdef int rc

        if self.closed:
            raise RuntimeError("Context has been destroyed")

        rc = zmq_ctx_get(self.handle, option)
        _check_rc(rc)

        return rc

    def destroy(self, linger=None):
        """ctx.destroy(linger=None)
        
        Close all sockets associated with this context, and then terminate
        the context. If linger is specified,
        the LINGER sockopt of the sockets will be set prior to closing.
        
        .. warning::
        
            destroy involves calling ``zmq_close()``, which is **NOT** threadsafe.
            If there are active sockets in other threads, this must not be called.
        """
        
        cdef int linger_c
        cdef bint setlinger=False
        
        if linger is not None:
            linger_c = linger
            setlinger=True

        if self.handle != NULL and not self.closed and self._n_sockets:
            while self._n_sockets:
                if setlinger:
                    zmq_setsockopt(self._sockets[0], ZMQ_LINGER, &linger_c, sizeof(int))
                rc = zmq_close(self._sockets[0])
                if rc < 0 and zmq_errno() != ZMQ_ENOTSOCK:
                    raise ZMQError()
                self._n_sockets -= 1
                self._sockets[0] = self._sockets[self._n_sockets]
        self.term()
    
__all__ = ['Context']
