"""0MQ Socket class."""

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
# Cython Imports
#-----------------------------------------------------------------------------

# get version-independent aliases:
cdef extern from "pyversion_compat.h":
    pass

from libc.errno cimport ENAMETOOLONG
from libc.string cimport memcpy

from cpython cimport PyBytes_FromStringAndSize
from cpython cimport PyBytes_AsString, PyBytes_Size
from cpython cimport Py_DECREF, Py_INCREF

from buffers cimport asbuffer_r, viewfromobject_r

from libzmq cimport *
from message cimport Frame, copy_zmq_msg_bytes

from context cimport Context

cdef extern from "Python.h":
    ctypedef int Py_ssize_t

cdef extern from "ipcmaxlen.h":
    int get_ipc_path_max_len()

cdef extern from "getpid_compat.h":
    int getpid()


#-----------------------------------------------------------------------------
# Python Imports
#-----------------------------------------------------------------------------

import copy as copy_mod
import time
import sys
import random
import struct
import codecs

from zmq.utils import jsonapi

try:
    import cPickle
    pickle = cPickle
except:
    cPickle = None
    import pickle

import zmq
from zmq.core import constants
from zmq.core.constants import *
from zmq.core.checkrc cimport _check_rc
from zmq.error import ZMQError, ZMQBindError
from zmq.utils.strtypes import bytes,unicode,basestring

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

IPC_PATH_MAX_LEN = get_ipc_path_max_len()

# inline some small socket submethods:
# true methods frequently cannot be inlined, acc. Cython docs

cdef inline _check_closed(Socket s, bint raise_notsup):
    cdef int rc
    cdef int errno
    cdef int stype
    cdef size_t sz=sizeof(int)
    if s._closed:
        if raise_notsup:
            raise ZMQError(ENOTSUP)
        else:
            return True
    else:
        rc = zmq_getsockopt(s.handle, ZMQ_TYPE, <void *>&stype, &sz)
        if rc < 0 and zmq_errno() == ENOTSOCK:
            s._closed = True
            if raise_notsup:
                raise ZMQError(ENOTSUP)
            else:
                return True
        else:
            _check_rc(rc)
    return False

cdef inline Frame _recv_frame(void *handle, int flags=0, track=False):
    """Receive a message in a non-copying manner and return a Frame."""
    cdef int rc
    cdef Frame msg
    msg = Frame(track=track)

    with nogil:
        rc = zmq_msg_recv(&msg.zmq_msg, handle, flags)
    
    _check_rc(rc)
    return msg

cdef inline object _recv_copy(void *handle, int flags=0):
    """Receive a message and return a copy"""
    cdef zmq_msg_t zmq_msg
    with nogil:
        zmq_msg_init (&zmq_msg)
        rc = zmq_msg_recv(&zmq_msg, handle, flags)
    _check_rc(rc)
    msg_bytes = copy_zmq_msg_bytes(&zmq_msg)
    with nogil:
        zmq_msg_close(&zmq_msg)
    return msg_bytes

cdef inline object _send_frame(void *handle, Frame msg, int flags=0):
    """Send a Frame on this socket in a non-copy manner."""
    cdef int rc
    cdef Frame msg_copy

    # Always copy so the original message isn't garbage collected.
    # This doesn't do a real copy, just a reference.
    msg_copy = msg.fast_copy()

    with nogil:
        rc = zmq_msg_send(&msg_copy.zmq_msg, handle, flags)

    _check_rc(rc)
    return msg.tracker


cdef inline object _send_copy(void *handle, object msg, int flags=0):
    """Send a message on this socket by copying its content."""
    cdef int rc, rc2
    cdef zmq_msg_t data
    cdef char *msg_c
    cdef Py_ssize_t msg_c_len=0

    # copy to c array:
    asbuffer_r(msg, <void **>&msg_c, &msg_c_len)

    # Copy the msg before sending. This avoids any complications with
    # the GIL, etc.
    # If zmq_msg_init_* fails we must not call zmq_msg_close (Bus Error)
    with nogil:
        rc = zmq_msg_init_size(&data, msg_c_len)

    _check_rc(rc)

    with nogil:
        memcpy(zmq_msg_data(&data), msg_c, zmq_msg_size(&data))
        rc = zmq_msg_send(&data, handle, flags)
        rc2 = zmq_msg_close(&data)
    _check_rc(rc)
    _check_rc(rc2)


cdef class Socket:
    """Socket(context, socket_type)

    A 0MQ socket.

    These objects will generally be constructed via the socket() method of a Context object.
    
    Note: 0MQ Sockets are *not* threadsafe. **DO NOT** share them across threads.
    
    Parameters
    ----------
    context : Context
        The 0MQ Context this Socket belongs to.
    socket_type : int
        The socket type, which can be any of the 0MQ socket types: 
        REQ, REP, PUB, SUB, PAIR, DEALER, ROUTER, PULL, PUSH, XPUB, XSUB.
    
    See Also
    --------
    .Context.socket : method for creating a socket bound to a Context.
    """

    def __cinit__(self, Context context, int socket_type, *args, **kwrags):
        cdef Py_ssize_t c_handle
        c_handle = context._handle

        self.handle = NULL
        self.context = context
        self.socket_type = socket_type
        with nogil:
            self.handle = zmq_socket(<void *>c_handle, socket_type)
        if self.handle == NULL:
            raise ZMQError()
        self._closed = False
        self._pid = getpid()
        context._add_socket(self.handle)

    def __dealloc__(self):
        """close *and* remove from context's list
        
        But be careful that context might not exist if called during gc
        """
        if self.handle != NULL and getpid() == self._pid:
            rc = zmq_close(self.handle)
            if rc != 0 and zmq_errno() != ENOTSOCK:
                # ignore ENOTSOCK (closed by Context)
                _check_rc(rc)
            # during gc, self.context might be NULL
            if self.context:
                self.context._remove_socket(self.handle)
    
    def __init__(self, context, socket_type):
        pass

    @property
    def closed(self):
        return _check_closed(self, False)
    
    def close(self, linger=None):
        """s.close(linger=None)

        Close the socket.
        
        If linger is specified, LINGER sockopt will be set prior to closing.

        This can be called to close the socket by hand. If this is not
        called, the socket will automatically be closed when it is
        garbage collected.
        """
        cdef int rc=0
        cdef int linger_c
        cdef bint setlinger=False
        
        if linger is not None:
            linger_c = linger
            setlinger=True
        
        if self.handle != NULL and not self._closed and getpid() == self._pid:
            if setlinger:
                zmq_setsockopt(self.handle, ZMQ_LINGER, &linger_c, sizeof(int))
            rc = zmq_close(self.handle)
            if rc != 0 and zmq_errno() != ENOTSOCK:
                # ignore ENOTSOCK (closed by Context)
                _check_rc(rc)
            self._closed = True
            # during gc, self.context might be NULL
            if self.context:
                self.context._remove_socket(self.handle)
            self.handle = NULL

    def set(self, int option, optval):
        """s.set(option, optval)

        Set socket options.

        See the 0MQ API documentation for details on specific options.

        Parameters
        ----------
        option : int
            The option to set.  Available values will depend on your
            version of libzmq.  Examples include::
            
                zmq.SUBSCRIBE, UNSUBSCRIBE, IDENTITY, HWM, LINGER, FD
        
        optval : int or bytes
            The value of the option to set.
        """
        cdef int64_t optval_int64_c
        cdef int optval_int_c
        cdef int rc
        cdef char* optval_c
        cdef Py_ssize_t sz

        _check_closed(self, True)
        if isinstance(optval, unicode):
            raise TypeError("unicode not allowed, use setsockopt_string")

        if option in zmq.constants.bytes_sockopts:
            if not isinstance(optval, bytes):
                raise TypeError('expected bytes, got: %r' % optval)
            optval_c = PyBytes_AsString(optval)
            sz = PyBytes_Size(optval)
            with nogil:
                rc = zmq_setsockopt(
                    self.handle, option,
                    optval_c, sz
                )
        elif option in zmq.constants.int64_sockopts:
            if not isinstance(optval, int):
                raise TypeError('expected int, got: %r' % optval)
            optval_int64_c = optval
            with nogil:
                rc = zmq_setsockopt(
                    self.handle, option,
                    &optval_int64_c, sizeof(int64_t)
                )
        else:
            # default is to assume int, which is what most new sockopts will be
            # this lets pyzmq work with newer libzmq which may add constants
            # pyzmq has not yet added, rather than artificially raising. Invalid
            # sockopts will still raise just the same, but it will be libzmq doing
            # the raising.
            if not isinstance(optval, int):
                raise TypeError('expected int, got: %r' % optval)
            optval_int_c = optval
            with nogil:
                rc = zmq_setsockopt(
                    self.handle, option,
                    &optval_int_c, sizeof(int)
                )

        _check_rc(rc)

    def get(self, int option):
        """s.get(option)

        Get the value of a socket option.

        See the 0MQ API documentation for details on specific options.

        Parameters
        ----------
        option : int
            The option to get.  Available values will depend on your
            version of libzmq.  Examples include::
            
                zmq.IDENTITY, HWM, LINGER, FD, EVENTS

        Returns
        -------
        optval : int or bytes
            The value of the option as a bytestring or int.
        """
        cdef int64_t optval_int64_c
        cdef int optval_int_c
        cdef fd_t optval_fd_c
        cdef char identity_str_c [255]
        cdef size_t sz
        cdef int rc

        _check_closed(self, True)

        if option in zmq.constants.bytes_sockopts:
            sz = 255
            with nogil:
                rc = zmq_getsockopt(self.handle, option, <void *>identity_str_c, &sz)
            _check_rc(rc)
            result = PyBytes_FromStringAndSize(<char *>identity_str_c, sz)
        elif option in zmq.constants.int64_sockopts:
            sz = sizeof(int64_t)
            with nogil:
                rc = zmq_getsockopt(self.handle, option, <void *>&optval_int64_c, &sz)
            _check_rc(rc)
            result = optval_int64_c
        elif option == ZMQ_FD:
            sz = sizeof(fd_t)
            with nogil:
                rc = zmq_getsockopt(self.handle, option, <void *>&optval_fd_c, &sz)
            _check_rc(rc)
            result = optval_fd_c
        else:
            # default is to assume int, which is what most new sockopts will be
            # this lets pyzmq work with newer libzmq which may add constants
            # pyzmq has not yet added, rather than artificially raising. Invalid
            # sockopts will still raise just the same, but it will be libzmq doing
            # the raising.
            sz = sizeof(int)
            with nogil:
                rc = zmq_getsockopt(self.handle, option, <void *>&optval_int_c, &sz)
            _check_rc(rc)
            result = optval_int_c

        return result
    
    def bind(self, addr):
        """s.bind(addr)

        Bind the socket to an address.

        This causes the socket to listen on a network port. Sockets on the
        other side of this connection will use ``Socket.connect(addr)`` to
        connect to this socket.

        Parameters
        ----------
        addr : str
            The address string. This has the form 'protocol://interface:port',
            for example 'tcp://127.0.0.1:5555'. Protocols supported include
            tcp, udp, pgm, epgm, inproc and ipc. If the address is unicode, it is
            encoded to utf-8 first.
        """
        cdef int rc
        cdef char* c_addr

        _check_closed(self, True)
        if isinstance(addr, unicode):
            addr = addr.encode('utf-8')
        if not isinstance(addr, bytes):
            raise TypeError('expected str, got: %r' % addr)
        c_addr = addr
        rc = zmq_bind(self.handle, c_addr)
        if rc != 0:
            if IPC_PATH_MAX_LEN and zmq_errno() == ENAMETOOLONG:
                # py3compat: addr is bytes, but msg wants str
                if str is unicode:
                    addr = addr.decode('utf-8', 'replace')
                path = addr.split('://', 1)[-1]
                msg = ('ipc path "{0}" is longer than {1} '
                                'characters (sizeof(sockaddr_un.sun_path)). '
                                'zmq.IPC_PATH_MAX_LEN constant can be used '
                                'to check addr length (if it is defined).'
                                .format(path, IPC_PATH_MAX_LEN))
                raise ZMQError(msg=msg)
        _check_rc(rc)

    def connect(self, addr):
        """s.connect(addr)

        Connect to a remote 0MQ socket.

        Parameters
        ----------
        addr : str
            The address string. This has the form 'protocol://interface:port',
            for example 'tcp://127.0.0.1:5555'. Protocols supported are
            tcp, upd, pgm, inproc and ipc. If the address is unicode, it is
            encoded to utf-8 first.
        """
        cdef int rc
        cdef char* c_addr

        _check_closed(self, True)
        if isinstance(addr, unicode):
            addr = addr.encode('utf-8')
        if not isinstance(addr, bytes):
            raise TypeError('expected str, got: %r' % addr)
        c_addr = addr
        
        rc = zmq_connect(self.handle, c_addr)
        if rc != 0:
            raise ZMQError()

    def unbind(self, addr):
        """s.unbind(addr)
        
        Unbind from an address (undoes a call to bind).
        
        This feature requires libzmq-3

        Parameters
        ----------
        addr : str
            The address string. This has the form 'protocol://interface:port',
            for example 'tcp://127.0.0.1:5555'. Protocols supported are
            tcp, upd, pgm, inproc and ipc. If the address is unicode, it is
            encoded to utf-8 first.
        """
        cdef int rc
        cdef char* c_addr
        
        if ZMQ_VERSION_MAJOR < 3:
            raise NotImplementedError("unbind requires libzmq >= 3.0, have %s" % zmq.zmq_version())
        

        _check_closed(self, True)
        if isinstance(addr, unicode):
            addr = addr.encode('utf-8')
        if not isinstance(addr, bytes):
            raise TypeError('expected str, got: %r' % addr)
        c_addr = addr
        
        rc = zmq_unbind(self.handle, c_addr)
        if rc != 0:
            raise ZMQError()

    def disconnect(self, addr):
        """s.disconnect(addr)

        Disconnect from a remote 0MQ socket (undoes a call to connect).
        
        This feature requires libzmq-3

        Parameters
        ----------
        addr : str
            The address string. This has the form 'protocol://interface:port',
            for example 'tcp://127.0.0.1:5555'. Protocols supported are
            tcp, upd, pgm, inproc and ipc. If the address is unicode, it is
            encoded to utf-8 first.
        """
        cdef int rc
        cdef char* c_addr
        
        if ZMQ_VERSION_MAJOR < 3:
            raise NotImplementedError("disconnect requires libzmq >= 3.0, have %s" % zmq.zmq_version())

        _check_closed(self, True)
        if isinstance(addr, unicode):
            addr = addr.encode('utf-8')
        if not isinstance(addr, bytes):
            raise TypeError('expected str, got: %r' % addr)
        c_addr = addr
        
        rc = zmq_disconnect(self.handle, c_addr)
        if rc != 0:
            raise ZMQError()

    #-------------------------------------------------------------------------
    # Sending and receiving messages
    #-------------------------------------------------------------------------

    cpdef object send(self, object data, int flags=0, copy=True, track=False):
        """s.send(data, flags=0, copy=True, track=False)

        Send a message on this socket.

        This queues the message to be sent by the IO thread at a later time.

        Parameters
        ----------
        data : object, str, Frame
            The content of the message.
        flags : int
            Any supported flag: NOBLOCK, SNDMORE.
        copy : bool
            Should the message be sent in a copying or non-copying manner.
        track : bool
            Should the message be tracked for notification that ZMQ has
            finished with it? (ignored if copy=True)

        Returns
        -------
        None : if `copy` or not track
            None if message was sent, raises an exception otherwise.
        MessageTracker : if track and not copy
            a MessageTracker object, whose `pending` property will
            be True until the send is completed.
        
        Raises
        ------
        TypeError
            If a unicode object is passed
        ValueError
            If `track=True`, but an untracked Frame is passed.
        ZMQError
            If the send does not succeed for any reason.
        
        """
        _check_closed(self, True)
        
        if isinstance(data, unicode):
            raise TypeError("unicode not allowed, use send_unicode")
        
        if copy:
            # msg.bytes never returns the input data object
            # it is always a copy, but always the same copy
            if isinstance(data, Frame):
                data = data.buffer
            return _send_copy(self.handle, data, flags)
        else:
            if isinstance(data, Frame):
                if track and not data.tracker:
                    raise ValueError('Not a tracked message')
                msg = data
            else:
                msg = Frame(data, track=track)
            return _send_frame(self.handle, msg, flags)

    cpdef object recv(self, int flags=0, copy=True, track=False):
        """s.recv(flags=0, copy=True, track=False)

        Receive a message.

        Parameters
        ----------
        flags : int
            Any supported flag: NOBLOCK. If NOBLOCK is set, this method
            will raise a ZMQError with EAGAIN if a message is not ready.
            If NOBLOCK is not set, then this method will block until a
            message arrives.
        copy : bool
            Should the message be received in a copying or non-copying manner?
            If False a Frame object is returned, if True a string copy of
            message is returned.
        track : bool
            Should the message be tracked for notification that ZMQ has
            finished with it? (ignored if copy=True)

        Returns
        -------
        msg : bytes, Frame
            The received message frame.  If `copy` is False, then it will be a Frame,
            otherwise it will be bytes.
            
        Raises
        ------
        ZMQError
            for any of the reasons zmq_msg_recv might fail.
        """
        _check_closed(self, True)
        
        if copy:
            return _recv_copy(self.handle, flags)
        else:
            frame = _recv_frame(self.handle, flags, track)
            frame.more = self.getsockopt(zmq.RCVMORE)
            return frame
    

__all__ = ['Socket', 'IPC_PATH_MAX_LEN']
