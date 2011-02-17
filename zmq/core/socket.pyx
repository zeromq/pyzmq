"""0MQ Socket class."""

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
# Cython Imports
#-----------------------------------------------------------------------------

# get version-independent aliases:
cdef extern from "pyversion_compat.h":
    pass

from libc.stdlib cimport free, malloc
from cpython cimport PyBytes_FromStringAndSize
from cpython cimport PyBytes_AsString, PyBytes_Size
from cpython cimport Py_DECREF, Py_INCREF

from buffers cimport asbuffer_r, frombuffer_r, viewfromobject_r

from czmq cimport *
from message cimport Message, copy_zmq_msg_bytes

cdef extern from "Python.h":
    ctypedef int Py_ssize_t

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

from zmq.core import constants
from zmq.core.constants import *
from zmq.core.error import ZMQError, ZMQBindError
from zmq.utils.strtypes import bytes,unicode,basestring

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

# inline some small socket submethods:
# true methods frequently cannot be inlined, acc. Cython docs

cdef inline _check_closed(Socket s):
    if s.closed:
        raise ZMQError(ENOTSUP)

cdef inline Message _recv_message(void *handle, int flags=0, track=False):
    """Receive a message in a non-copying manner and return a Message."""
    cdef int rc
    cdef Message msg
    msg = Message(track=track)

    with nogil:
        rc = zmq_recv(handle, &msg.zmq_msg, flags)

    if rc != 0:
        raise ZMQError()
    return msg

cdef inline object _recv_copy(void *handle, int flags=0):
    """Recieve a message and return a copy"""
    cdef zmq_msg_t zmq_msg
    with nogil:
        zmq_msg_init (&zmq_msg)
        rc = zmq_recv(handle, &zmq_msg, flags)
    if rc != 0:
        raise ZMQError()
    msg_bytes = copy_zmq_msg_bytes(&zmq_msg)
    with nogil:
        zmq_msg_close(&zmq_msg)
    return msg_bytes

cdef inline object _send_message(void *handle, Message msg, int flags=0):
    """Send a Message on this socket in a non-copy manner."""
    cdef int rc
    cdef Message msg_copy

    # Always copy so the original message isn't garbage collected.
    # This doesn't do a real copy, just a reference.
    msg_copy = msg.fast_copy()

    with nogil:
        rc = zmq_send(handle, &msg_copy.zmq_msg, flags)

    if rc != 0:
        # don't pop from the Queue here, because the free_fn will
        #  still call Queue.get() even if the send fails
        raise ZMQError()
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
        memcpy(zmq_msg_data(&data), msg_c, zmq_msg_size(&data))

    if rc != 0:
        raise ZMQError()

    with nogil:
        rc = zmq_send(handle, &data, flags)
        rc2 = zmq_msg_close(&data)

    if rc != 0 or rc2 != 0:
        raise ZMQError()


cdef class Socket:
    """Socket(context, socket_type)

    A 0MQ socket.

    These objects will generally be constructed via the socket() method of a Context object.
    
    Parameters
    ----------
    context : Context
        The 0MQ Context this Socket belongs to.
    socket_type : int
        The socket type, which can be any of the 0MQ socket types: 
        REQ, REP, PUB, SUB, PAIR, XREQ, XREP, PULL, PUSH, XPUB, XSUB.
    
    See Also
    --------
    .Context.socket : method for creating a socket bound to a Context.
    """

    def __cinit__(self, object context, int socket_type):
        cdef Py_ssize_t c_handle
        c_handle = context._handle

        self.handle = NULL
        self.context = context
        self.socket_type = socket_type
        with nogil:
            self.handle = zmq_socket(<void *>c_handle, socket_type)
        if self.handle == NULL:
            raise ZMQError()
        self.closed = False

    def __dealloc__(self):
        self.close()

    def close(self):
        """s.close()

        Close the socket.

        This can be called to close the socket by hand. If this is not
        called, the socket will automatically be closed when it is
        garbage collected.
        """
        cdef int rc
        if self.handle != NULL and not self.closed:
            with nogil:
                rc = zmq_close(self.handle)
            if rc != 0:
                raise ZMQError()
            self.handle = NULL
            self.closed = True

    def setsockopt(self, int option, optval):
        """s.setsockopt(option, optval)

        Set socket options.

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : str
            The name of the option to set. Can be any of: SUBSCRIBE, 
            UNSUBSCRIBE, IDENTITY, HWM, SWAP, AFFINITY, RATE, 
            RECOVERY_IVL, MCAST_LOOP, SNDBUF, RCVBUF.
        optval : int or str
            The value of the option to set.
        """
        cdef int64_t optval_int64_c
        cdef int optval_int_c
        cdef int rc
        cdef char* optval_c
        cdef Py_ssize_t sz

        _check_closed(self)
        if isinstance(optval, unicode):
            raise TypeError("unicode not allowed, use setsockopt_unicode")

        if option in constants.bytes_sockopts:
            if not isinstance(optval, bytes):
                raise TypeError('expected str, got: %r' % optval)
            optval_c = PyBytes_AsString(optval)
            sz = PyBytes_Size(optval)
            with nogil:
                rc = zmq_setsockopt(
                    self.handle, option,
                    optval_c, sz
                )
        elif option in constants.int64_sockopts:
            if not isinstance(optval, int):
                raise TypeError('expected int, got: %r' % optval)
            optval_int64_c = optval
            with nogil:
                rc = zmq_setsockopt(
                    self.handle, option,
                    &optval_int64_c, sizeof(int64_t)
                )
        elif option in constants.int_sockopts:
            if not isinstance(optval, int):
                raise TypeError('expected int, got: %r' % optval)
            optval_int_c = optval
            with nogil:
                rc = zmq_setsockopt(
                    self.handle, option,
                    &optval_int_c, sizeof(int)
                )
        else:
            raise ZMQError(EINVAL)

        if rc != 0:
            raise ZMQError()

    def getsockopt(self, int option):
        """s.getsockopt(option)

        Get the value of a socket option.

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : str
            The name of the option to set. Can be any of: 
            IDENTITY, HWM, SWAP, AFFINITY, RATE, 
            RECOVERY_IVL, MCAST_LOOP, SNDBUF, RCVBUF, RCVMORE.

        Returns
        -------
        optval : int, str
            The value of the option as a string or int.
        """
        cdef int64_t optval_int64_c
        cdef int optval_int_c
        cdef char identity_str_c [255]
        cdef size_t sz
        cdef int rc

        _check_closed(self)

        if option in constants.bytes_sockopts:
            sz = 255
            with nogil:
                rc = zmq_getsockopt(self.handle, option, <void *>identity_str_c, &sz)
            if rc != 0:
                raise ZMQError()
            result = PyBytes_FromStringAndSize(<char *>identity_str_c, sz)
        elif option in  constants.int64_sockopts:
            sz = sizeof(int64_t)
            with nogil:
                rc = zmq_getsockopt(self.handle, option, <void *>&optval_int64_c, &sz)
            if rc != 0:
                raise ZMQError()
            result = optval_int64_c
        elif option in constants.int_sockopts:
            sz = sizeof(int)
            with nogil:
                rc = zmq_getsockopt(self.handle, option, <void *>&optval_int_c, &sz)
            if rc != 0:
                raise ZMQError()
            result = optval_int_c
        else:
            raise ZMQError(EINVAL)

        return result
    
    def setsockopt_unicode(self, int option, optval, encoding='utf-8'):
        """s.setsockopt_unicode(option, optval, encoding='utf-8')

        Set socket options with a unicode object it is simply a wrapper
        for setsockopt to protect from encoding ambiguity.

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : int
            The name of the option to set. Can be any of: SUBSCRIBE, 
            UNSUBSCRIBE, IDENTITY
        optval : unicode
            The value of the option to set.
        encoding : str
            The encoding to be used, default is utf8
        """
        if not isinstance(optval, unicode):
            raise TypeError("unicode strings only")
        return self.setsockopt(option, optval.encode(encoding))
    
    def getsockopt_unicode(self, int option, encoding='utf-8'):
        """s.getsockopt_unicode(option, encoding='utf-8')

        Get the value of a socket option.

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : unicode string
            The name of the option to set. Can be any of: 
            IDENTITY, HWM, SWAP, AFFINITY, RATE, 
            RECOVERY_IVL, MCAST_LOOP, SNDBUF, RCVBUF, RCVMORE.

        Returns
        -------
        optval : unicode
            The value of the option as a unicode string.
        """
        if option not in [IDENTITY]:
            raise TypeError("option %i will not return a string to be decoded"%option)
        return self.getsockopt(option).decode(encoding)
    
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
            for example 'tcp://127.0.0.1:5555'. Protocols supported are
            tcp, upd, pgm, inproc and ipc. If the address is unicode, it is
            encoded to utf-8 first.
        """
        cdef int rc

        _check_closed(self)
        if isinstance(addr, unicode):
            addr = addr.encode('utf-8')
        if not isinstance(addr, bytes):
            raise TypeError('expected str, got: %r' % addr)
        with nogil:
            rc = zmq_bind(self.handle, addr)
        if rc != 0:
            raise ZMQError()

    def bind_to_random_port(self, addr, min_port=2000, max_port=20000, max_tries=100):
        """s.bind_to_random_port(addr, min_port=2000, max_port=20000, max_tries=100)

        Bind this socket to a random port in a range.

        Parameters
        ----------
        addr : str
            The address string without the port to pass to ``Socket.bind()``.
        min_port : int, optional
            The minimum port in the range of ports to try.
        max_port : int, optional
            The maximum port in the range of ports to try.
        max_tries : int, optional
            The number of attempt to bind.

        Returns
        -------
        port : int
            The port the socket was bound to.
        
        Raises
        ------
        ZMQBindError
            if `max_tries` reached before successful bind
        """
        for i in range(max_tries):
            try:
                port = random.randrange(min_port, max_port)
                self.bind('%s:%s' % (addr, port))
            except ZMQError:
                pass
            else:
                return port
        raise ZMQBindError("Could not bind socket to random port.")

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

        _check_closed(self)
        if isinstance(addr, unicode):
            addr = addr.encode('utf-8')
        if not isinstance(addr, bytes):
            raise TypeError('expected str, got: %r' % addr)
        with nogil:
            rc = zmq_connect(self.handle, addr)
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
        data : object, str, Message
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
            If `track=True`, but an untracked Message is passed.
        ZMQError
            If the send does not succeed for any reason.
        
        """
        _check_closed(self)
        
        if isinstance(data, unicode):
            raise TypeError("unicode not allowed, use send_unicode")
        
        if copy:
            # msg.bytes never returns the input data object
            # it is always a copy, but always the same copy
            if isinstance(data, Message):
                data = data.buffer
            return _send_copy(self.handle, data, flags)
        else:
            if isinstance(data, Message):
                if track and not data.tracker:
                    raise ValueError('Not a tracked message')
                msg = data
            else:
                msg = Message(data, track=track)
            return _send_message(self.handle, msg, flags)

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
            If False a Message object is returned, if True a string copy of
            message is returned.
        track : bool
            Should the message be tracked for notification that ZMQ has
            finished with it? (ignored if copy=True)

        Returns
        -------
        msg : str, Message
            The returned message.  If `copy` is False, then it will be a Message,
            otherwise a str.
            
        Raises
        ------
        ZMQError
            for any of the reasons zmq_recv might fail.
        """
        _check_closed(self)
        
        if copy:
            return _recv_copy(self.handle, flags)
        else:
            return _recv_message(self.handle, flags, track)
    
    def send_multipart(self, msg_parts, int flags=0, copy=True, track=False):
        """s.send_multipart(msg_parts, flags=0, copy=True, track=False)

        Send a sequence of messages as a multipart message.

        Parameters
        ----------
        msg_parts : iterable
            A sequence of messages to send as a multipart message. Each element
            can be any sendable object (Message, bytes, buffer-providers)
        flags : int, optional
            Only the NOBLOCK flagis supported, SNDMORE is handled
            automatically.
        copy : bool, optional
            Should the message(s) be sent in a copying or non-copying manner.
        track : bool, optional
            Should the message(s) be tracked for notification that ZMQ has
            finished with it (ignored if copy=True).
        
        Returns
        -------
        None : if copy or not track
        MessageTracker : if track and not copy
            a MessageTracker object, whose `pending` property will
            be True until the last send is completed.
        """
        for msg in msg_parts[:-1]:
            self.send(msg, SNDMORE|flags, copy=copy, track=track)
        # Send the last part without the extra SNDMORE flag.
        return self.send(msg_parts[-1], flags, copy=copy, track=track)

    def recv_multipart(self, int flags=0, copy=True, track=False):
        """s.recv_multipart(flags=0, copy=True, track=False)

        Receive a multipart message as a list of messages.

        Parameters
        ----------
        flags : int, optional
            Any supported flag: NOBLOCK. If NOBLOCK is set, this method
            will raise a ZMQError with EAGAIN if a message is not ready.
            If NOBLOCK is not set, then this method will block until a
            message arrives.
        copy : bool, optional
            Should the message(s) be received in a copying or non-copying manner?
            If False a Message object is returned for part, if True a string copy of
            message is returned for each message part.
        track : bool, optional
            Should the message(s) be tracked for notification that ZMQ has
            finished with it? (ignored if copy=True)
        
        Returns
        -------
        msg_parts : list
            A list of messages in the multipart message; either Messages or strs,
            depending on `copy`.
        """
        parts = []
        while True:
            part = self.recv(flags, copy=copy, track=track)
            parts.append(part)
            if self.rcvmore():
                continue
            else:
                break
        return parts

    def rcvmore(self):
        """s.rcvmore()

        Are there more parts to a multipart message?
        
        Returns
        -------
        more : bool
            whether we are in the middle of a multipart message.
        """
        more = self.getsockopt(RCVMORE)
        return bool(more)

    def send_unicode(self, u, int flags=0, copy=False, encoding='utf-8'):
        """s.send_unicode(u, flags=0, copy=False, encoding='utf-8')

        Send a Python unicode object as a message with an encoding.

        Parameters
        ----------
        u : Python unicode object
            The unicode string to send.
        flags : int, optional
            Any valid send flag.
        encoding : str [default: 'utf-8']
            The encoding to be used
        """
        if not isinstance(u, basestring):
            raise TypeError("unicode/str objects only")
        return self.send(u.encode(encoding), flags=flags, copy=copy)
    
    def recv_unicode(self, int flags=0, encoding='utf-8'):
        """s.recv_unicode(flags=0, encoding='utf-8')

        Receive a unicode string, as sent by send_unicode.
        
        Parameters
        ----------
        flags : int
            Any valid recv flag.
        encoding : str [default: 'utf-8']
            The encoding to be used

        Returns
        -------
        s : unicode string
            The Python unicode string that arrives as message bytes.
        """
        msg = self.recv(flags=flags, copy=False)
        return codecs.decode(msg.bytes, encoding)
    
    def send_pyobj(self, obj, flags=0, protocol=-1):
        """s.send_pyobj(obj, flags=0, protocol=-1)

        Send a Python object as a message using pickle to serialize.

        Parameters
        ----------
        obj : Python object
            The Python object to send.
        flags : int
            Any valid send flag.
        protocol : int
            The pickle protocol number to use. Default of -1 will select
            the highest supported number. Use 0 for multiple platform
            support.
        """
        msg = pickle.dumps(obj, protocol)
        return self.send(msg, flags)

    def recv_pyobj(self, flags=0):
        """s.recv_pyobj(flags=0)

        Receive a Python object as a message using pickle to serialize.

        Parameters
        ----------
        flags : int
            Any valid recv flag.

        Returns
        -------
        obj : Python object
            The Python object that arrives as a message.
        """
        s = self.recv(flags)
        return pickle.loads(s)

    def send_json(self, obj, flags=0):
        """s.send_json(obj, flags=0)

        Send a Python object as a message using json to serialize.

        Parameters
        ----------
        obj : Python object
            The Python object to send.
        flags : int
            Any valid send flag.
        """
        if jsonapi.jsonmod is None:
            raise ImportError('jsonlib{1,2}, json or simplejson library is required.')
        else:
            msg = jsonapi.dumps(obj)
            return self.send(msg, flags)

    def recv_json(self, flags=0):
        """s.recv_json(flags=0)

        Receive a Python object as a message using json to serialize.

        Parameters
        ----------
        flags : int
            Any valid recv flag.

        Returns
        -------
        obj : Python object
            The Python object that arrives as a message.
        """
        if jsonapi.jsonmod is None:
            raise ImportError('jsonlib{1,2}, json or simplejson library is required.')
        else:
            msg = self.recv(flags)
            return jsonapi.loads(msg)


__all__ = ['Socket']
