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

from libc.stdlib cimport free, malloc
from cpython cimport PyString_FromStringAndSize
from cpython cimport PyString_AsString, PyString_Size
from cpython cimport Py_DECREF, Py_INCREF
from cpython cimport bool

from allocate cimport allocate
from buffers cimport asbuffer_r, frombuffer_r, viewfromobject_r

cdef extern from "Python.h":
    ctypedef int Py_ssize_t
    cdef void PyEval_InitThreads()

# It seems that in only *some* version of Python/Cython we need to call this
# by hand to get threads initialized. Not clear why this is the case though.
# If we don't have this, pyzmq will segfault.
PyEval_InitThreads()

import copy as copy_mod
import time
import random
import struct
import codecs

try:    # 3.x
    from queue import Queue, Empty
except: # 2.x
    from Queue import Queue, Empty

try:
    import cjson
    json = cjson
    raise ImportError
except ImportError:
    cjson = None
    try:
        import json
    except:
        try:
            import simplejson as json
        except ImportError:
            json = None

try:
    import cPickle
    pickle = cPickle
except:
    cPickle = None
    import pickle

def jsonify(o): 
    return json.dumps(o, separators=(',',':'))

if cjson is not None:
    from_json = json.decode
    to_json = json.encode
else:
    to_json = jsonify
    from_json = json.loads

#-----------------------------------------------------------------------------
# Python module level constants
#-----------------------------------------------------------------------------

NOBLOCK = ZMQ_NOBLOCK
PAIR = ZMQ_PAIR
PUB = ZMQ_PUB
SUB = ZMQ_SUB
REQ = ZMQ_REQ
REP = ZMQ_REP
XREQ = ZMQ_XREQ
XREP = ZMQ_XREP
PULL = ZMQ_PULL
PUSH = ZMQ_PUSH
UPSTREAM = ZMQ_UPSTREAM
DOWNSTREAM = ZMQ_DOWNSTREAM
HWM = ZMQ_HWM
SWAP = ZMQ_SWAP
AFFINITY = ZMQ_AFFINITY
IDENTITY = ZMQ_IDENTITY
SUBSCRIBE = ZMQ_SUBSCRIBE
UNSUBSCRIBE = ZMQ_UNSUBSCRIBE
RATE = ZMQ_RATE
RECOVERY_IVL = ZMQ_RECOVERY_IVL
MCAST_LOOP = ZMQ_MCAST_LOOP
SNDBUF = ZMQ_SNDBUF
RCVBUF = ZMQ_RCVBUF
RCVMORE = ZMQ_RCVMORE
SNDMORE = ZMQ_SNDMORE
POLLIN = ZMQ_POLLIN
POLLOUT = ZMQ_POLLOUT
POLLERR = ZMQ_POLLERR
STREAMER = ZMQ_STREAMER
FORWARDER = ZMQ_FORWARDER
QUEUE = ZMQ_QUEUE


#-----------------------------------------------------------------------------
# Error handling
#-----------------------------------------------------------------------------

# Often used (these are alse in errno.)
EAGAIN = ZMQ_EAGAIN
EINVAL = ZMQ_EINVAL
EFAULT = ZMQ_EFAULT
ENOMEM = ZMQ_ENOMEM
ENODEV = ZMQ_ENODEV

# For Windows compatability
ENOTSUP = ZMQ_ENOTSUP
EPROTONOSUPPORT = ZMQ_EPROTONOSUPPORT
ENOBUFS = ZMQ_ENOBUFS
ENETDOWN = ZMQ_ENETDOWN
EADDRINUSE = ZMQ_EADDRINUSE
EADDRNOTAVAIL = ZMQ_EADDRNOTAVAIL
ECONNREFUSED = ZMQ_ECONNREFUSED
EINPROGRESS = ZMQ_EINPROGRESS

# 0MQ Native
EMTHREAD = ZMQ_EMTHREAD
EFSM = ZMQ_EFSM
ENOCOMPATPROTO = ZMQ_ENOCOMPATPROTO
ETERM = ZMQ_ETERM


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

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def zmq_version():
    """Return the version of ZeroMQ itself."""
    cdef int major, minor, patch
    _zmq_version(&major, &minor, &patch)
    return '%i.%i.%i' % (major, minor, patch)


cdef void free_python_msg(void *data, void *hint) with gil:
    """A function for DECREF'ing Python based messages."""
    if hint != NULL:
        tracker_queue = (<tuple>hint)[1]
        Py_DECREF(<object>hint)
        if isinstance(tracker_queue, Queue):
            # don't assert before DECREF:
            # assert tracker_queue.empty(), "somebody else wrote to my Queue!"
            tracker_queue.put(0)
        tracker_queue = None


cdef class MessageTracker(object):
    """A class for tracking if 0MQ is done using one or more messages.

    When you send a 0MQ mesage, it is not sent immeidately. The 0MQ IO thread
    send the message at some later time. Often you want to know when 0MQ has
    actually sent the message though. This is complicated by the fact that
    a single 0MQ message can be sent multiple times using differen sockets.
    This class allows you to track all of the 0MQ usages of a message.
    """

    def __init__(self, *towatch):
        """Create a message tracker to track a set of mesages.

        Parameters
        ----------
        *towatch : tuple of Queue, MessageTracker, Message instances.
            This list of objects to track. This class can track the low-level
            Queues used by the Message class, other MessageTrackers or 
            actual Messsages.
        """
        self.queues = set()
        self.peers = set()
        for obj in towatch:
            if isinstance(obj, Queue):
                self.queues.add(obj)
            elif isinstance(obj, MessageTracker):
                self.peers.add(obj)
            elif isinstance(obj, Message):
                self.peers.add(obj.tracker)
            else:
                raise TypeError("Require Queues or Messages, not %s"%type(obj))
    
    @property
    def done(self):
        """Is 0MQ completely done with the messages being tracked."""
        for queue in self.queues:
            if queue.empty():
                return False
        for pm in self.peers:
            if not pm.done:
                return False
        return True
    
    def wait(self, timeout=-1):
        """Wait until 0MQ is completely done with the messages, then return.

        Parameters
        ----------
        timeout : int
            Maximum time in (s) to wait before raising NotDone.

        Returns
        -------
        Raises NotDone if `timeout` reached before I am done.
        """
        tic = time.time()
        if timeout is False or timeout < 0:
            remaining = 3600*24*7 # a week
        else:
            remaining = timeout
        done = False
        try:
            for queue in self.queues:
                if remaining < 0:
                    raise NotDone
                queue.get(timeout=remaining)
                queue.put(0)
                toc = time.time()
                remaining -= (toc-tic)
                tic = toc
        except Empty:
            raise NotDone
        
        for peer in self.peers:
            if remaining < 0:
                raise NotDone
            peer.wait(timeout=remaining)
            toc = time.time()
            remaining -= (toc-tic)
            tic = toc
    
    def old_wait(self):
        while not self.done:
            time.sleep(.001)


cdef class Message:
    """A Message class for non-copy send/recvs.

    This class is only needed if you want to do non-copying send and recvs.
    When you pass a string to this class, like ``Message(s)``, the 
    ref-count of s is increased by two: once because Message saves s as 
    an instance attribute and another because a ZMQ message is created that
    points to the buffer of s. This second ref-count increase makes sure
    that s lives until all messages that use it have been sent. Once 0MQ
    sends all the messages and it doesn't need the buffer of s, 0MQ will call
    Py_DECREF(s).
    """

    def __cinit__(self, object data=None):
        cdef int rc
        cdef char *data_c = NULL
        cdef Py_ssize_t data_len_c
        cdef object hint

        # Save the data object in case the user wants the the data as a str.
        self._data = data
        self._failed_init = True  # bool switch for dealloc
        self._buffer = None       # buffer view of data
        self._bytes = None        # bytes copy of data

        # Queue and MessageTracker for monitoring when zmq is done with data:
        self.tracker_queue = Queue()
        self.tracker = MessageTracker(self.tracker_queue)

        if isinstance(data, unicode):
            raise TypeError("Unicode objects not allowed. Only: str/bytes, buffer interfaces.")

        if data is None:
            with nogil:
                rc = zmq_msg_init(&self.zmq_msg)
            if rc != 0:
                raise ZMQError()
            self._failed_init = False
            return
        else:
            asbuffer_r(data, <void **>&data_c, &data_len_c)
        # We INCREF the *original* Python object (not self) and pass it
        # as the hint below. This allows other copies of this Message
        # object to take over the ref counting of data properly.
        hint = (data, self.tracker_queue)
        Py_INCREF(hint)
        with nogil:
            rc = zmq_msg_init_data(
                &self.zmq_msg, <void *>data_c, data_len_c, 
                <zmq_free_fn *>free_python_msg, <void *>hint
            )
        if rc != 0:
            Py_DECREF(hint)
            raise ZMQError()
        self._failed_init = False

    def __dealloc__(self):
        cdef int rc
        if self._failed_init:
            return
        # This simply decreases the 0MQ ref-count of zmq_msg.
        rc = zmq_msg_close(&self.zmq_msg)
        if rc != 0:
            raise ZMQError()

    def __copy__(self):
        """Create a shallow copy of the message.

        This does not copy the contents of the Message, just the pointer.
        This will increment the 0MQ ref count of the message, but not
        the ref count of the Python object. That is only done once when
        the Python is first turned into a 0MQ message.
        """
        return self.fast_copy()

    cdef Message fast_copy(self):
        """Fast, cdef'd version of shallow copy of the message."""
        cdef Message new_msg
        new_msg = Message()
        # This does not copy the contents, but just increases the ref-count 
        # of the zmq_msg by one.
        zmq_msg_copy(&new_msg.zmq_msg, &self.zmq_msg)
        # Copy the ref to data so the copy won't create a copy when str is
        # called.
        if self._data is not None:
            new_msg._data = self._data
        if self._buffer is not None:
            new_msg._buffer = self._buffer
        if self._bytes is not None:
            new_msg._bytes = self._bytes
        # Message copies share the tracker and tracker_queue.
        new_msg.tracker_queue = self.tracker_queue
        new_msg.tracker = self.tracker
        return new_msg

    def __len__(self):
        """Return the length of the message in bytes."""
        return <int>zmq_msg_size(&self.zmq_msg)

    def __str__(self):
        """Return the str form of the message."""
        if isinstance(self._data, str):
            return self._data
        else:
            return str(self.bytes)
    
    @property
    def done(self):
        """Is 0MQ completely done with the message?"""
        return self.tracker.done
    
    def wait(self, timeout=-1):
        """Wait for 0MQ to be done with the message, or until timeout.
        
        Parameters
        ----------
        timeout : int
            Maximum time in (s) to wait before raising NotDone.
        
        Raises NotDone if ``timeout`` reached before I am done.
        """
        return self.tracker.wait(timeout=timeout)

    
    cdef object _getbuffer(self):
        """Create a Python buffer/view of the message data.

        This will be called only once, the first time the ``buffer`` property
        is accessed. Subsequent calls use a cached copy.
        """
        cdef char *data_c = NULL
        cdef Py_ssize_t data_len_c
        # read-only, because we don't want to allow
        # editing of the message in-place
        if self._data is None:
            # return buffer on input object, to preserve refcounting
            data_c = <char *>zmq_msg_data(&self.zmq_msg)
            data_len_c = zmq_msg_size(&self.zmq_msg)
            return frombuffer_r(data_c, data_len_c)
        else:
            return viewfromobject_r(self._data)
    
    @property
    def buffer(self):
        """Get a read-only buffer view of the message contents."""
        if self._buffer is None:
            self._buffer = self._getbuffer()
        return self._buffer

    cdef object _copybytes(self):
        """Create a Python bytes object from a copy of the message data.

        This will be called only once, the first time the ``bytes`` property
        is accessed. Subsequent calls use a cached copy.
        """
        cdef char *data_c = NULL
        cdef Py_ssize_t data_len_c
        # always make a copy:
        data_c = <char *>zmq_msg_data(&self.zmq_msg)
        data_len_c = zmq_msg_size(&self.zmq_msg)
        return PyString_FromStringAndSize(data_c, data_len_c)
    
    @property
    def bytes(self):
        """Get the message content as a Python str/bytes object.

        The first time this property is accessed, a copy of the message 
        contents is made. From then on that same copy of the message is
        returned.
        """
        if self._bytes is None:
            self._bytes = self._copybytes()
        return self._bytes


cdef class Context:
    """Manage the lifecycle of a 0MQ context.

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
        self.handle = zmq_init(io_threads)
        if self.handle == NULL:
            raise ZMQError()
        self.closed = False

    def __dealloc__(self):
        cdef int rc
        if self.handle != NULL:
            rc = zmq_term(self.handle)
            if rc != 0:
                raise ZMQError()

    def term(self):
        """Close or terminate the context.

        This can be called to close the context by hand. If this is not
        called, the context will automatically be closed when it is
        garbage collected.
        """
        cdef int rc
        if self.handle != NULL and not self.closed:
            rc = zmq_term(self.handle)
            if rc != 0:
                raise ZMQError()
            self.handle = NULL
            self.closed = True

    def socket(self, int socket_type):
        """Create a Socket associated with this Context.

        Parameters
        ----------
        socket_type : int
            The socket type, which can be any of the 0MQ socket types: 
            REQ, REP, PUB, SUB, PAIR, XREQ, XREP, PULL, PUSH.
        """
        if self.closed:
            raise ZMQError(ENOTSUP)
        return Socket(self, socket_type)


cdef class Socket:
    """A 0MQ socket.

    Socket(context, socket_type)

    Parameters
    ----------
    context : Context
        The 0MQ Context this Socket belongs to.
    socket_type : int
        The socket type, which can be any of the 0MQ socket types: 
        REQ, REP, PUB, SUB, PAIR, XREQ, XREP, PULL, PUSH.
    """

    def __cinit__(self, Context context, int socket_type):
        self.handle = NULL
        self.context = context
        self.socket_type = socket_type
        self.handle = zmq_socket(context.handle, socket_type)
        if self.handle == NULL:
            raise ZMQError()
        self.closed = False

    def __dealloc__(self):
        self.close()

    def close(self):
        """Close the socket.

        This can be called to close the socket by hand. If this is not
        called, the socket will automatically be closed when it is
        garbage collected.
        """
        cdef int rc
        if self.handle != NULL and not self.closed:
            rc = zmq_close(self.handle)
            if rc != 0:
                raise ZMQError()
            self.handle = NULL
            self.closed = True

    def _check_closed(self):
        if self.closed:
            raise ZMQError(ENOTSUP)

    def setsockopt(self, int option, optval):
        """Set socket options.

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
        cdef int64_t optval_int_c
        cdef int rc

        self._check_closed()
        if isinstance(optval, unicode):
            raise TypeError("unicode not allowed, use setsockopt_unicode")

        if option in [SUBSCRIBE, UNSUBSCRIBE, IDENTITY]:
            if not isinstance(optval, str):
                raise TypeError('expected str, got: %r' % optval)
            rc = zmq_setsockopt(
                self.handle, option,
                PyString_AsString(optval), PyString_Size(optval)
            )
        elif option in [HWM, SWAP, AFFINITY, RATE, RECOVERY_IVL,
                        MCAST_LOOP, SNDBUF, RCVBUF]:
            if not isinstance(optval, int):
                raise TypeError('expected int, got: %r' % optval)
            optval_int_c = optval
            rc = zmq_setsockopt(
                self.handle, option,
                &optval_int_c, sizeof(int64_t)
            )
        else:
            raise ZMQError(EINVAL)

        if rc != 0:
            raise ZMQError()

    def getsockopt(self, int option):
        """Get the value of a socket option.

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : str
            The name of the option to set. Can be any of: 
            IDENTITY, HWM, SWAP, AFFINITY, RATE, 
            RECOVERY_IVL, MCAST_LOOP, SNDBUF, RCVBUF, RCVMORE.

        Returns
        -------
        The value of the option as a string or int.
        """
        cdef int64_t optval_int_c
        cdef char identity_str_c [255]
        cdef size_t sz
        cdef int rc

        self._check_closed()

        if option in [IDENTITY]:
            sz = 255
            rc = zmq_getsockopt(self.handle, option, <void *>identity_str_c, &sz)
            if rc != 0:
                raise ZMQError()
            result = PyString_FromStringAndSize(<char *>identity_str_c, sz)
        elif option in [HWM, SWAP, AFFINITY, RATE, RECOVERY_IVL,
                        MCAST_LOOP, SNDBUF, RCVBUF, RCVMORE]:
            sz = sizeof(int64_t)
            rc = zmq_getsockopt(self.handle, option, <void *>&optval_int_c, &sz)
            if rc != 0:
                raise ZMQError()
            result = optval_int_c
        else:
            raise ZMQError()

        return result
    
    def setsockopt_unicode(self, int option, optval, encoding='utf-8'):
        """Set socket options with a unicode object it is simply a wrapper 
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
    
    def getsockopt_unicode(self, int option,encoding='utf-8'):
        """Get the value of a socket option.

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : unicode string
            The name of the option to set. Can be any of: 
            IDENTITY, HWM, SWAP, AFFINITY, RATE, 
            RECOVERY_IVL, MCAST_LOOP, SNDBUF, RCVBUF, RCVMORE.

        Returns
        -------
        The value of the option as a string or int.
        """
        if option not in [IDENTITY]:
            raise TypeError("option %i will not return a string to be decoded"%option)
        return self.getsockopt(option).decode(encoding)
    
    def bind(self, addr):
        """Bind the socket to an address.

        This causes the socket to listen on a network port. Sockets on the
        other side of this connection will use :meth:`Sockiet.connect` to
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

        self._check_closed()
        if isinstance(addr, unicode):
            addr = addr.encode('utf-8')
        if not isinstance(addr, str):
            raise TypeError('expected str, got: %r' % addr)
        rc = zmq_bind(self.handle, addr)
        if rc != 0:
            raise ZMQError()

    def bind_to_random_port(self, addr, min_port=2000, max_port=20000, max_tries=100):
        """Bind this socket to a random port in a range.

        Parameters
        ----------
        addr : str
            The address string without the port to pass to :meth:`Socket.bind`.
        min_port : int
            The minimum port in the range of ports to try.
        max_port : int
            The maximum port in the range of ports to try.
        max_tries : int
            The number of attempt to bind.

        Returns
        -------
        port : int
            The port the socket was bound to.
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
        """Connect to a remote 0MQ socket.

        Parameters
        ----------
        addr : str
            The address string. This has the form 'protocol://interface:port',
            for example 'tcp://127.0.0.1:5555'. Protocols supported are
            tcp, upd, pgm, inproc and ipc. If the address is unicode, it is
            encoded to utf-8 first.
        """
        cdef int rc

        self._check_closed()
        if isinstance(addr, unicode):
            addr = addr.encode('utf-8')
        if not isinstance(addr, str):
            raise TypeError('expected str, got: %r' % addr)
        rc = zmq_connect(self.handle, addr)
        if rc != 0:
            raise ZMQError()

    #-------------------------------------------------------------------------
    # Sending and receiving messages
    #-------------------------------------------------------------------------

    def send(self, object data, int flags=0, bool copy=True):
        """Send a message on this socket.

        This queues the message to be sent by the IO thread at a later time.

        Parameters
        ----------
        data : object, str, Message
            The content of the message.
        flags : int
            Any supported flag: NOBLOCK, SNDMORE.
        copy : bool
            Should the message be sent in a copying or non-copying manner.

        Returns
        -------
        if copy:
            None if message was sent, raises an exception otherwise.
        else:
            a class:`MessageTracker` object, whose ``pending`` property will
            be ``True`` until the send is completed.
        """
        self._check_closed()
        
        if isinstance(data, unicode):
            raise TypeError("unicode not allowed, use send_unicode")
        
        if copy:
            # msg.bytes never returns the input data object
            # it is always a copy, but always the same copy
            if isinstance(data, Message):
                data = data.buffer
            return self._send_copy(data, flags)
        else:
            if isinstance(data, Message):
                msg = data
            else:
                msg = Message(data)
            return self._send_message(msg, flags)

    def _send_message(self, Message msg, int flags=0):
        """Send a Message on this socket in a non-copy manner."""
        cdef int rc
        cdef Message msg_copy

        # Always copy so the original message isn't garbage collected.
        # This doesn't do a real copy, just a reference.
        msg_copy = msg.fast_copy()
        
        with nogil:
            rc = zmq_send(self.handle, &msg_copy.zmq_msg, flags)

        if rc != 0:
            msg.tracker_queue.get()
            raise ZMQError()
        return msg.tracker
            

    def _send_copy(self, object msg, int flags=0):
        """Send a message on this socket by copying its content."""
        cdef int rc, rc2
        cdef zmq_msg_t data
        cdef char *msg_c
        cdef Py_ssize_t msg_c_len
        
        # copy to c array:
        asbuffer_r(msg, <void **>&msg_c, &msg_c_len)
        
        # Copy the msg before sending. This avoids any complications with
        # the GIL, etc.
        # If zmq_msg_init_* fails we must not call zmq_msg_close (Bus Error)
        rc = zmq_msg_init_size(&data, msg_c_len)
        memcpy(zmq_msg_data(&data), msg_c, zmq_msg_size(&data))

        if rc != 0:
            raise ZMQError()

        with nogil:
            rc = zmq_send(self.handle, &data, flags)
        rc2 = zmq_msg_close(&data)

        if rc != 0 or rc2 != 0:
            raise ZMQError()
    
    def recv(self, int flags=0, copy=True):
        """Receive a message.

        Parameters
        ----------
        flags : int
            Any supported flag: NOBLOCK. If NOBLOCK is set, this method
            will return None if a message is not ready. If NOBLOCK is not
            set, then this method will block until a message arrives.
        copy : bool
            Should the message be received in a copying or non-copying manner.
            If False a Message object is returned, if True a string copy of
            message is returned.
        Returns
        -------
        msg : str
            The returned message, or raises ZMQError otherwise.
        """
        self._check_closed()
        
        m = self._recv_message(flags)
        
        if copy:
            return m.bytes
        else:
            return m
    
    def _recv_message(self, int flags=0):
        """Receive a message in a non-copying manner and return a Message."""
        cdef int rc
        cdef Message msg
        msg = Message()

        with nogil:
            rc = zmq_recv(self.handle, &msg.zmq_msg, flags)

        if rc != 0:
            raise ZMQError()
        return msg

    def send_multipart(self, msg_parts, int flags=0, copy=True):
        """Send a sequence of messages as a multipart message.

        Parameters
        ----------
        msg_parts : iterable
            A sequence of messages to send as a multipart message.
        flags : int
            Only the NOBLOCK flagis supported, SNDMORE is handled
            automatically.
        """
        for msg in msg_parts[:-1]:
            self.send(msg, SNDMORE|flags, copy=copy)
        # Send the last part without the extra SNDMORE flag.
        return self.send(msg_parts[-1], flags, copy=copy)

    def recv_multipart(self, int flags=0, copy=True):
        """Receive a multipart message as a list of messages.

        Parameters
        ----------
        flags : int
            Any supported flag: NOBLOCK. If NOBLOCK is set, this method
            will return None if a message is not ready. If NOBLOCK is not
            set, then this method will block until a message arrives.

        Returns
        -------
        msg_parts : list
            A list of messages in the multipart message.
        """
        parts = []
        while True:
            part = self.recv(flags, copy=copy)
            parts.append(part)
            if self.rcvmore():
                continue
            else:
                break
        return parts

    def rcvmore(self):
        """Are there more parts to a multipart message."""
        more = self.getsockopt(RCVMORE)
        return bool(more)

    def send_unicode(self, u, int flags=0, copy=False, encoding='utf-8'):
        """Send a Python unicode object as a message with an encoding.

        Parameters
        ----------
        u : Python unicode object
            The unicode string to send.
        flags : int
            Any valid send flag.
        encoding : str
            The encoding to be used, default is 'utf-8'
        """
        if not isinstance(u, basestring):
            raise TypeError("unicode/str objects only")
        return self.send(u.encode(encoding), flags=flags, copy=copy)
    
    def recv_unicode(self, int flags=0,encoding='utf-8'):
        """Receive a unicode string, as sent by send_unicode.
        
        Parameters
        ----------
        flags : int
            Any valid recv flag.
        encoding : str
            The encoding to be used, default is 'utf-8'

        Returns
        -------
        s : unicode string
            The Python unicode string that arrives as message bytes.
        """
        msg = self.recv(flags=flags, copy=False)
        return codecs.decode(msg.buffer, encoding)
    
    def send_pyobj(self, obj, flags=0, protocol=-1):
        """Send a Python object as a message using pickle to serialize.

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
        """Receive a Python object as a message using pickle to serialize.

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
        """Send a Python object as a message using json to serialize.

        Parameters
        ----------
        obj : Python object
            The Python object to send.
        flags : int
            Any valid send flag.
        """
        if json is None:
            raise ImportError('cjson, json or simplejson library is required.')
        else:
            msg = to_json(obj)
            return self.send(msg, flags)

    def recv_json(self, flags=0):
        """Receive a Python object as a message using json to serialize.

        Parameters
        ----------
        flags : int
            Any valid recv flag.

        Returns
        -------
        obj : Python object
            The Python object that arrives as a message.
        """
        if json is None:
            raise ImportError('cjson, json or simplejson library is required.')
        else:
            msg = self.recv(flags)
            return from_json(msg)


cdef class Stopwatch:
    """A simple stopwatch based on zmq_stopwatch_start/stop.

    This class should be used for benchmarking and timing ØMQ code.
    """
    def __cinit__(self):
        self.watch = NULL

    def __dealloc__(self):
        try:
            self.stop()
        except ZMQError:
            pass

    def start(self):
        """Start the stopwatch."""
        if self.watch == NULL:
            self.watch = zmq_stopwatch_start()
        else:
            raise ZMQError('Stopwatch is already runing.')

    def stop(self):
        """Stop the stopwatch."""
        if self.watch == NULL:
            raise ZMQError('Must start the Stopwatch before calling stop.')
        else:
            time = zmq_stopwatch_stop(self.watch)
            self.watch = NULL
            return time

    def sleep(self, int seconds):
        """Sleep for a number of seconds."""
        zmq_sleep(seconds)

#-----------------------------------------------------------------------------
# Polling related methods
#-----------------------------------------------------------------------------

def _poll(sockets, long timeout=-1):
    """Poll a set of 0MQ sockets, native file descs. or sockets.

    Parameters
    ----------
    sockets : list of tuples of (socket, flags)
        Each element of this list is a two-tuple containing a socket
        and a flags. The socket may be a 0MQ socket or any object with
        a :meth:`fileno` method. The flags can be zmq.POLLIN (for detecting
        for incoming messages), zmq.POLLOUT (for detecting that send is OK)
        or zmq.POLLIN|zmq.POLLOUT for detecting both.
    timeout : int
        The number of microseconds to poll for. Negative means no timeout.
    """
    cdef int rc, i
    cdef zmq_pollitem_t *pollitems = NULL
    cdef int nsockets = len(sockets)
    cdef Socket current_socket
    pollitems_o = allocate(nsockets*sizeof(zmq_pollitem_t),<void**>&pollitems)

    for i in range(nsockets):
        s = sockets[i][0]
        events = sockets[i][1]
        if isinstance(s, Socket):
            current_socket = s
            pollitems[i].socket = current_socket.handle
            pollitems[i].events = events
            pollitems[i].revents = 0
        elif isinstance(s, int):
            pollitems[i].socket = NULL
            pollitems[i].fd = s
            pollitems[i].events = events
            pollitems[i].revents = 0
        elif hasattr(s, 'fileno'):
            try:
                fileno = int(s.fileno())
            except:
                raise ValueError('fileno() must return an valid integer fd')
            else:
                pollitems[i].socket = NULL
                pollitems[i].fd = fileno
                pollitems[i].events = events
                pollitems[i].revents = 0
        else:
            raise TypeError(
                "Socket must be a 0MQ socket, an integer fd or have "
                "a fileno() method: %r" % s
            )

    with nogil:
        rc = zmq_poll(pollitems, nsockets, timeout)
    if rc == -1:
        raise ZMQError()

    results = []
    for i in range(nsockets):
        s = sockets[i][0]
        # Return the fd for sockets, for compat. with select.poll.
        if hasattr(s, 'fileno'):
            s = s.fileno()
        revents = pollitems[i].revents
        # Only return sockets with non-zero status for compat. with select.poll.
        if revents > 0:
            results.append((s, revents))

    return results


class Poller(object):
    """An stateful poll interface that mirrors Python's built-in poll."""

    def __init__(self):
        self.sockets = {}

    def register(self, socket, flags=POLLIN|POLLOUT):
        """Register a 0MQ socket or native fd for I/O monitoring.

        Parameters
        ----------
        socket : zmq.Socket or native socket
            A zmq.Socket or any Python object having a :meth:`fileno` 
            method that returns a valid file descriptor.
        flags : int
            The events to watch for.  Can be POLLIN, POLLOUT or POLLIN|POLLOUT.
        """
        self.sockets[socket] = flags

    def modify(self, socket, flags=POLLIN|POLLOUT):
        """Modify the flags for an already registered 0MQ socket or native fd."""
        self.register(socket, flags)

    def unregister(self, socket):
        """Remove a 0MQ socket or native fd for I/O monitoring.

        Parameters
        ----------
        socket : Socket
            The socket instance to stop polling.
        """
        del self.sockets[socket]

    def poll(self, timeout=None):
        """Poll the registered 0MQ or native fds for I/O.

        Parameters
        ----------
        timeout : float, int
            The timeout in milliseconds. If None, no timeout (infinite). This
            is in milliseconds to be compatible with :func:`select.poll`. The
            underlying zmq_poll uses microseconds and we convert to that in
            this function.
        """
        if timeout is None:
            timeout = -1
        # Convert from ms -> us for zmq_poll.
        timeout = int(timeout*1000.0)
        if timeout < 0:
            timeout = -1
        return _poll(self.sockets.items(), timeout=timeout)


def select(rlist, wlist, xlist, timeout=None):
    """Return the result of poll as a lists of sockets ready for r/w.

    This has the same interface as Python's built-in :func:`select` function.

    Parameters
    ----------
    timeout : float, int
        The timeout in seconds. This is in seconds to be compatible with
        :func:`select.select`. The underlying zmq_poll uses microseconds and
        we convert to that in this function.
    """
    if timeout is None:
        timeout = -1
    # Convert from sec -> us for zmq_poll.
    timeout = int(timeout*1000000.0)
    if timeout < 0:
        timeout = -1
    sockets = []
    for s in set(rlist + wlist + xlist):
        flags = 0
        if s in rlist:
            flags |= POLLIN
        if s in wlist:
            flags |= POLLOUT
        if s in xlist:
            flags |= POLLERR
        sockets.append((s, flags))
    return_sockets = _poll(sockets, timeout)
    rlist, wlist, xlist = [], [], []
    for s, flags in return_sockets:
        if flags & POLLIN:
            rlist.append(s)
        if flags & POLLOUT:
            wlist.append(s)
        if flags & POLLERR:
            xlist.append(s)
    return rlist, wlist, xlist

#-----------------------------------------------------------------------------
# Basic device API
#-----------------------------------------------------------------------------

def device(int device_type, Socket isocket, Socket osocket):
    """Start a zeromq device.

    Parameters
    ----------
    device_type : (QUEUE, FORWARDER, STREAMER)
        The type of device to start.
    isocket : Socket
        The Socket instance for the incoming traffic.
    osocket : Socket
        The Socket instance for the outbound traffic.
    """
    cdef int result = 0
    with nogil:
        result = zmq_device(device_type, isocket.handle, osocket.handle)
    return result

#-----------------------------------------------------------------------------
# Symbols to export
#-----------------------------------------------------------------------------

__all__ = [
    'zmq_version',
    'NotDone',
    'MessageTracker',
    'Message',
    'Context',
    'Socket',
    'Stopwatch',
    'ZMQBaseError',
    'ZMQError',
    'ZMQBindError',
    'NOBLOCK',
    'PAIR',
    'PUB',
    'SUB',
    'REQ',
    'REP',
    'XREQ',
    'XREP',
    'PULL',
    'PUSH',
    'UPSTREAM',
    'DOWNSTREAM',
    'HWM',
    'SWAP',
    'AFFINITY',
    'IDENTITY',
    'SUBSCRIBE',
    'UNSUBSCRIBE',
    'RATE',
    'RECOVERY_IVL',
    'MCAST_LOOP',
    'SNDBUF',
    'RCVBUF',
    'SNDMORE',
    'RCVMORE',
    'POLLIN',
    'POLLOUT',
    'POLLERR',
    '_poll',
    'select',
    'STREAMER',
    'FORWARDER',
    'QUEUE',
    'device',
    'Poller',
    # ERRORNO codes
    'EAGAIN',
    'EINVAL',
    'ENOTSUP',
    'EPROTONOSUPPORT',
    'ENOBUFS',
    'ENETDOWN',
    'EADDRINUSE',
    'EADDRNOTAVAIL',
    'ECONNREFUSED',
    'EINPROGRESS',
    'EMTHREAD',
    'EFSM',
    'ENOCOMPATPROTO',
    'ETERM',
    'EFAULT',
    'ENOMEM',
    'ENODEV'
]

