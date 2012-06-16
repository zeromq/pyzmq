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

from os import getpid

from error import ZMQError
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
        
        self.sockopts = {}
        self._attrs = {}
        self._pid = getpid()

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
    
    @property
    def _socket_class(self):
        # import here to prevent circular import
        from zmq.core.socket import Socket
        return Socket
    
    def socket(self, int socket_type):
        """ctx.socket(socket_type)

        Create a Socket associated with this Context.

        Parameters
        ----------
        socket_type : int
            The socket type, which can be any of the 0MQ socket types: 
            REQ, REP, PUB, SUB, PAIR, DEALER, ROUTER, PULL, PUSH, XSUB, XPUB.
        """
        if self.closed:
            raise ZMQError(ENOTSUP)
        s = self._socket_class(self, socket_type)
        for opt, value in self.sockopts.iteritems():
            try:
                s.setsockopt(opt, value)
            except ZMQError:
                # ignore ZMQErrors, which are likely for socket options
                # that do not apply to a particular socket type, e.g.
                # SUBSCRIBE for non-SUB sockets.
                pass
        return s
    
    def __setattr__(self, key, value):
        """set default sockopts as attributes"""
        try:
            opt = getattr(constants, key.upper())
        except AttributeError:
            # allow subclasses to have extended attributes
            if self.__class__.__module__ != 'zmq.core.context':
                self._attrs[key] = value
            else:
                raise AttributeError("No such socket option: %s" % key.upper())
        else:
            self.sockopts[opt] = value
    
    def __getattr__(self, key):
        """get default sockopts as attributes"""
        if key in self._attrs:
            # `key` is subclass extended attribute
            return self._attrs[key]
        key = key.upper()
        try:
            opt = getattr(constants, key)
        except AttributeError:
            raise AttributeError("no such socket option: %s" % key)
        else:
            if opt not in self.sockopts:
                raise AttributeError(key)
            else:
                return self.sockopts[opt]
    
    def __delattr__(self, key):
        """delete default sockopts as attributes"""
        if key in self._attrs:
            # `key` is subclass extended attribute
            del self._attrs[key]
            return
        key = key.upper()
        try:
            opt = getattr(constants, key)
        except AttributeError:
            raise AttributeError("no such socket option: %s" % key)
        else:
            if opt not in self.sockopts:
                raise AttributeError(key)
            else:
                del self.sockopts[opt]
    
    @property
    def _handle(self):
        return <Py_ssize_t> self.handle

__all__ = ['Context']
