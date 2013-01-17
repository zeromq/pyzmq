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

from libzmq cimport *

cdef extern from "getpid_compat.h":
    int getpid()

from zmq.error import ZMQError
from zmq.core import constants
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
        if not io_threads >= 0:
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
        
        self.sockopts = {}
        self._attrs = {}
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
            self.n_sockets = 0
        self.term()
    
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
    
    @property
    def _handle(self):
        return <Py_ssize_t> self.handle
    
    def term(self):
        """ctx.term()

        Close or terminate the context.
        
        This can be called to close the context by hand. If this is not called,
        the context will automatically be closed when it is garbage collected.
        """
        cdef int rc
        cdef int i=-1

        if self.handle != NULL and not self.closed and getpid() == self._pid:
            with nogil:
                rc = zmq_term(self.handle)
            if rc != 0:
                raise ZMQError()
            self.handle = NULL
            self.closed = True

    def destroy(self, linger=None):
        """ctx.destroy(linger=None)
        
        Close all sockets associated with this context, and then terminate
        the context. If linger is specified,
        the LINGER sockopt of the sockets will be set prior to closing.
        
        WARNING:
        
        destroy involves calling zmq_close(), which is *NOT* threadsafe.
        If there are active sockets in other threads, this must not be called.
        """
        
        cdef int linger_c
        cdef bint setlinger=False
        
        if linger is not None:
            linger_c = linger
            setlinger=True
        if self.handle != NULL and not self.closed and self.n_sockets:
            while self.n_sockets:
                if setlinger:
                    zmq_setsockopt(self._sockets[0], ZMQ_LINGER, &linger_c, sizeof(int))
                rc = zmq_close(self._sockets[0])
                if rc != 0 and zmq_errno() != ENOTSOCK:
                    raise ZMQError()
                self.n_sockets -= 1
                self._sockets[0] = self._sockets[self.n_sockets]
            self.term()
    
__all__ = ['Context']
