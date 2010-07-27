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


from stdlib cimport *
from python_string cimport PyString_FromStringAndSize
from python_string cimport PyString_AsStringAndSize
from python_string cimport PyString_AsString, PyString_Size
from python_ref cimport Py_DECREF, Py_INCREF

cdef extern from "Python.h":
    ctypedef int Py_ssize_t
    cdef void PyEval_InitThreads()
    # 

# For some reason we need to call this.  My guess is that we are not doing
# any Python treading.
PyEval_InitThreads()

import copy as copy_mod
import random
import struct

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

include "allocate.pxi"
include "asbuffer.pxi"
include "frombuffer.pxi"

#-----------------------------------------------------------------------------
# Import the C header files
#-----------------------------------------------------------------------------
# unused unicode imports:
# from python_unicode cimport PyUnicode_FromEncodedObject
# cdef extern from "unicodeobject.h":
#     # this should be in Cython's python_unicode.pxd, but it isn't
#     cdef object PyUnicode_FromStringAndSize(char *ptr, Py_ssize_t size)

cdef extern from "errno.h" nogil:
    enum: ZMQ_EINVAL "EINVAL"
    enum: ZMQ_EAGAIN "EAGAIN"

cdef extern from "string.h" nogil:
    void *memcpy(void *dest, void *src, size_t n)
    size_t strlen(char *s)

cdef extern from "zmq_compat.h":
    ctypedef signed long long int64_t "pyzmq_int64_t"

cdef extern from "zmq.h" nogil:
    enum: ZMQ_HAUSNUMERO
    enum: ZMQ_ENOTSUP "ENOTSUP"
    enum: ZMQ_EPROTONOSUPPORT "EPROTONOSUPPORT"
    enum: ZMQ_ENOBUFS "ENOBUFS"
    enum: ZMQ_ENETDOWN "ENETDOWN"
    enum: ZMQ_EADDRINUSE "EADDRINUSE"
    enum: ZMQ_EADDRNOTAVAIL "EADDRNOTAVAIL"
    enum: ZMQ_ECONNREFUSED "ECONNREFUSED"
    enum: ZMQ_EINPROGRESS "EINPROGRESS"
    enum: ZMQ_EMTHREAD "EMTHREAD"
    enum: ZMQ_EFSM "EFSM"
    enum: ZMQ_ENOCOMPATPROTO "ENOCOMPATPROTO"
    enum: ZMQ_ETERM "ETERM"
    
    enum: errno
    char *zmq_strerror (int errnum)
    int zmq_errno()

    enum: ZMQ_MAX_VSM_SIZE # 30
    enum: ZMQ_DELIMITER # 31
    enum: ZMQ_VSM # 32

    ctypedef struct zmq_msg_t:
        void *content
        unsigned char shared
        unsigned char vsm_size
        unsigned char vsm_data [ZMQ_MAX_VSM_SIZE]
    
    ctypedef void zmq_free_fn(void *data, void *hint)
    
    int zmq_msg_init (zmq_msg_t *msg)
    int zmq_msg_init_size (zmq_msg_t *msg, size_t size)
    int zmq_msg_init_data (zmq_msg_t *msg, void *data,
        size_t size, zmq_free_fn *ffn, void *hint)
    int zmq_msg_close (zmq_msg_t *msg)
    int zmq_msg_move (zmq_msg_t *dest, zmq_msg_t *src)
    int zmq_msg_copy (zmq_msg_t *dest, zmq_msg_t *src)
    void *zmq_msg_data (zmq_msg_t *msg)
    size_t zmq_msg_size (zmq_msg_t *msg)

    void *zmq_init (int io_threads)
    int zmq_term (void *context)

    enum: ZMQ_PAIR # 0
    enum: ZMQ_PUB # 1
    enum: ZMQ_SUB # 2
    enum: ZMQ_REQ # 3
    enum: ZMQ_REP # 4
    enum: ZMQ_XREQ # 5
    enum: ZMQ_XREP # 6
    enum: ZMQ_UPSTREAM # 7
    enum: ZMQ_DOWNSTREAM # 8

    enum: ZMQ_HWM # 1
    enum: ZMQ_SWAP # 3
    enum: ZMQ_AFFINITY # 4
    enum: ZMQ_IDENTITY # 5
    enum: ZMQ_SUBSCRIBE # 6
    enum: ZMQ_UNSUBSCRIBE # 7
    enum: ZMQ_RATE # 8
    enum: ZMQ_RECOVERY_IVL # 9
    enum: ZMQ_MCAST_LOOP # 10
    enum: ZMQ_SNDBUF # 11
    enum: ZMQ_RCVBUF # 12
    enum: ZMQ_RCVMORE # 13

    enum: ZMQ_NOBLOCK # 1
    enum: ZMQ_SNDMORE # 2

    void *zmq_socket (void *context, int type)
    int zmq_close (void *s)
    int zmq_setsockopt (void *s, int option, void *optval, size_t optvallen)
    int zmq_getsockopt (void *s, int option, void *optval, size_t *optvallen)
    int zmq_bind (void *s, char *addr)
    int zmq_connect (void *s, char *addr)
    int zmq_send (void *s, zmq_msg_t *msg, int flags)
    int zmq_recv (void *s, zmq_msg_t *msg, int flags)
    
    enum: ZMQ_POLLIN # 1
    enum: ZMQ_POLLOUT # 2
    enum: ZMQ_POLLERR # 4

    ctypedef struct zmq_pollitem_t:
        void *socket
        int fd
        # #if defined _WIN32
        #     SOCKET fd;
        short events
        short revents

    ctypedef struct zmq_msg_t:
        void *content
        unsigned char flags
        unsigned char vsm_size
        unsigned char vsm_data [ZMQ_MAX_VSM_SIZE]
    
    int zmq_poll (zmq_pollitem_t *items, int nitems, long timeout)

    enum: ZMQ_STREAMER # 1
    enum: ZMQ_FORWARDER # 2
    enum: ZMQ_QUEUE # 3
    
    int zmq_device (int device, void * insocket, void * outsocket)
    
    # void *zmq_stopwatch_start ()
    # unsigned long zmq_stopwatch_stop (void *watch_)
    # void zmq_sleep (int seconds_)

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
            self.errstr = strerror(error)
            self.errno = error
        else:
            self.errstr = str(error)
            self.errno = None 

    def __str__(self):
        return self.errstr

class ZMQBindError(ZMQBaseError):
    """An error for bind_to_random_port."""
    pass

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


cdef void free_python_msg(void *data, void *hint) with gil:
    """A function for DECREF'ing Python based messages."""
    if hint != NULL:
        Py_DECREF(<object>hint)


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

    cdef zmq_msg_t zmq_msg
    cdef object data
    cdef object buf
    
    def __cinit__(self, object data=None):
        cdef int rc
        # Save the data object in case the user wants the the data as a str.
        self.data = data
        self.buf = None
        cdef char *data_c = NULL
        cdef Py_ssize_t data_len_c

        if data is None:
            with nogil:
                rc = zmq_msg_init(&self.zmq_msg)
            if rc != 0:
                raise ZMQError()
            return
        if isinstance(data, str):
            PyString_AsStringAndSize(data, &data_c, &data_len_c)
        elif isinstance(data, unicode):
            try: # simple string
                PyString_AsStringAndSize(data, &data_c, &data_len_c)
            except:
                asbuffer_r(data, <void **>&data_c, &data_len_c)
        else:
            # always use buffer interface?
            asbuffer_r(data, <void **>&data_c, &data_len_c)
        # We INCREF the *original* Python object (not self) and pass it
        # as the hint below. This allows other copies of this Message
        # object to take over the ref counting of data properly.
        Py_INCREF(data)
        with nogil:
            rc = zmq_msg_init_data(
                &self.zmq_msg, <void *>data_c, data_len_c, 
                <zmq_free_fn *>free_python_msg, <void *>data
            )
        if rc != 0:
            Py_DECREF(data)
            raise ZMQError()

    def __dealloc__(self):
        cdef int rc
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
        if self.data is not None:
            new_msg.data = self.data
        if self.buf is not None:
            new_msg.buf = self.buf
        return new_msg

    def __len__(self):
        """Return the length of the message in bytes."""
        return <int>zmq_msg_size(&self.zmq_msg)

    def __str__(self):
        """Return the str form of the message."""
        cdef char *data_c = NULL
        cdef Py_ssize_t data_len_c
        if self.data is None or not isinstance(self.data, (str, unicode)):
            data_c = <char *>zmq_msg_data(&self.zmq_msg)
            data_len_c = zmq_msg_size(&self.zmq_msg)
            return PyString_FromStringAndSize(data_c, data_len_c)
            # unused:
            # try:
            #     # PyString_FromStringAndSize won't fail if we get utf16 buffer
            #     # so we can't tell if the String is correct
            #     # PyUnicode_FromStringAndSize will raise an error
            #     # if we try to read a utf16 buffer as something else
            #     return PyUnicode_FromStringAndSize(data_c, data_len_c)
            # except:
            #     try:
            #         return PyUnicode_FromEncodedObject(self.buffer, 'utf16', NULL)
            #     except:
            #         return PyString_FromStringAndSize(data_c, data_len_c)
        # else:
        return self.data
    
    cdef object _getbuffer(self):
        cdef char *data_c = NULL
        cdef Py_ssize_t data_len_c
        data_c = <char *>zmq_msg_data(&self.zmq_msg)
        data_len_c = zmq_msg_size(&self.zmq_msg)
        # read-only, because we don't want to allow
        # editing of the message in-place
        self.buf = frombuffer_r(data_c, data_len_c)
    
    @property
    def buffer(self):
        if self.buf is None:
            self._getbuffer()
        return self.buf


cdef class Context:
    """Manage the lifecycle of a 0MQ context.

    This class no longer takes any flags or the number of application
    threads.

    Parameters
    ----------
    io_threads : int
        The number of IO threads.
    """

    cdef void *handle

    def __cinit__(self, int io_threads=1):
        self.handle = NULL
        if not io_threads > 0:
            raise ZMQError(EINVAL)
        self.handle = zmq_init(io_threads)
        if self.handle == NULL:
            raise ZMQError()

    def __dealloc__(self):
        cdef int rc
        if self.handle != NULL:
            rc = zmq_term(self.handle)
            if rc != 0:
                raise ZMQError()

    def socket(self, int socket_type):
        """Create a Socket associated with this Context.

        Parameters
        ----------
        socket_type : int
            The socket type, which can be any of the 0MQ socket types: 
            REQ, REP, PUB, SUB, PAIR, XREQ, XREP, UPSTREAM, DOWNSTREAM.
        """
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
        REQ, REP, PUB, SUB, PAIR, XREQ, XREP, UPSTREAM, DOWNSTREAM.
    """

    cdef void *handle
    cdef public int socket_type
    # Hold on to a reference to the context to make sure it is not garbage
    # collected until the socket it done with it.
    cdef public Context context
    cdef public object closed

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

        if option in [SUBSCRIBE, UNSUBSCRIBE, IDENTITY]:
            if not isinstance(optval, (str,unicode)):
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
            tcp, upd, pgm, inproc and ipc.
        """
        cdef int rc

        self._check_closed()

        if not isinstance(addr, (str,unicode)):
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
            tcp, upd, pgm, inproc and ipc.
        """
        cdef int rc

        self._check_closed()

        if not isinstance(addr, (str,unicode)):
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
        None if message was sent, raises an exception otherwise.
        """
        self._check_closed()
        if isinstance(data, Message):
            return self._send_message(data, flags)
        elif copy:
            return self._send_copy(data, flags)
        else:
            # I am not sure which non-copy implemntation to use here.
            # It probably doesn't matter though.
            msg = Message(data)
            return self._send_message(msg, flags)
            # return self._send_nocopy(msg, flags)

    def _send_message(self, Message msg, int flags=0):
        """Send a Message on this socket in a non-copy manner."""
        cdef int rc
        cdef Message msg_copy

        # Always copy so the original message isn't garbage collected.
        # This doesn't do a real copy, just a reference.
        msg_copy = msg.fast_copy()
        # msg_copy = copy_mod.copy(msg)
        with nogil:
            rc = zmq_send(self.handle, &msg.zmq_msg, flags)

        if rc != 0:
            raise ZMQError()

    def _send_copy(self, object msg, int flags=0):
        """Send a message on this socket by copying its content."""
        cdef int rc, rc2
        cdef zmq_msg_t data
        cdef char *msg_c
        cdef Py_ssize_t msg_c_len

        if isinstance(msg, str):
            PyString_AsStringAndSize(msg, &msg_c, &msg_c_len)
        elif isinstance(msg, unicode):
            try: # simple string
                PyString_AsStringAndSize(msg, &msg_c, &msg_c_len)
            except: # utf16 buffer
                asbuffer_r(msg, <void **>&msg_c, &msg_c_len)
        else: # buffer interface (numpy, etc.)
            asbuffer_r(msg, <void **>&msg_c, &msg_c_len)
            
        # Copy the msg before sending. This avoids any complications with
        # the GIL, etc.
        # If zmq_msg_init_* fails do we need to call zmq_msg_close?
        rc = zmq_msg_init_size(&data, msg_c_len)
        memcpy(zmq_msg_data(&data), msg_c, zmq_msg_size(&data))

        if rc != 0:
            raise ZMQError()

        with nogil:
            rc = zmq_send(self.handle, &data, flags)
        rc2 = zmq_msg_close(&data)

        # Shouldn't the error handling for zmq_msg_close come after that
        # of zmq_send?
        if rc2 != 0:
            raise ZMQError()

        if rc != 0:
            raise ZMQError()

    def _send_nocopy(self, object msg, int flags=0):
        """Send a Python string on this socket in a non-copy manner.

        This method is not being used currently, as the same functionality
        is provided by self._send_message(Message(data)). This may eventually
        be removed.
        """
        cdef int rc
        cdef zmq_msg_t data
        cdef char *msg_c
        cdef Py_ssize_t msg_c_len

        if not isinstance(msg, (str,unicode)):
            raise TypeError('expected str, got: %r' % msg)

        try:
            PyString_AsStringAndSize(msg, &msg_c, &msg_c_len)
        except:
            asbuffer_r(msg, <void **>&msg_c, &msg_c_len)
        Py_INCREF(msg) # We INCREF to prevent Python from gc'ing msg
        rc = zmq_msg_init_data(
            &data, <void *>msg_c, msg_c_len,
            <zmq_free_fn *>free_python_msg, <void *>msg
        )

        if rc != 0:
            # If zmq_msg_init_data fails it does not call zmq_free_fn, 
            # so we Py_DECREF.
            Py_DECREF(msg)
            raise ZMQError()

        with nogil:
            rc = zmq_send(self.handle, &data, flags)

        if rc != 0:
            # If zmq_send fails it does not call zmq_free_fn, so we Py_DECREF.
            Py_DECREF(msg)
            zmq_msg_close(&data)
            raise ZMQError()

        rc = zmq_msg_close(&data)
        if rc != 0:
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
            If True a Message object is returned, if False a string copy of 
            message is returned.
        Returns
        -------
        msg : str
            The returned message, or raises ZMQError otherwise.
        """
        self._check_closed()
        if copy:
            # This could be implemented by simple calling _recv_message and
            # then casting to a str.
            return self._recv_copy(flags)
        else:
            return self._recv_message(flags)

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

    def _recv_copy(self, int flags=0):
        """Receive a message in a copying manner as a string."""
        cdef int rc
        cdef zmq_msg_t data

        rc = zmq_msg_init(&data)
        if rc != 0:
            raise ZMQError()

        with nogil:
            rc = zmq_recv(self.handle, &data, flags)

        if rc != 0:
            raise ZMQError()

        try:
            msg = PyString_FromStringAndSize(
                <char *>zmq_msg_data(&data), 
                zmq_msg_size(&data)
            )
        finally:
            rc = zmq_msg_close(&data)

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
        # Send the last part without the SNDMORE flag.
        self.send(msg_parts[-1], flags)

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


# cdef class Stopwatch:
#     """A simple stopwatch based on zmq_stopwatch_start/stop."""
# 
#     cdef void *watch
# 
#     def __cinit__(self):
#         self.watch = NULL
# 
#     def __dealloc__(self):
#         try:
#             self.stop()
#         except ZMQError:
#             pass
# 
#     def start(self):
#         if self.watch == NULL:
#             self.watch = zmq_stopwatch_start()
#         else:
#             raise ZMQError('Stopwatch is already runing.')
# 
#     def stop(self):
#         if self.watch == NULL:
#             raise ZMQError('Must start the Stopwatch before calling stop.')
#         else:
#             time = zmq_stopwatch_stop(self.watch)
#             self.watch = NULL
#             return time
# 
#     def sleep(self, int seconds):
#         zmq_sleep(seconds)


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

    # int zmq_poll (zmq_pollitem_t *items, int nitems, long timeout)
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
    

########### monitored_queue adapted from zmq::queue.cpp #######
# basic free for msg_init_data:
cdef void z_free (void *data, void *hint) nogil:
    free (data)

# the MonitoredQueue C function:
cdef int monitored_queue_ (void *insocket_, void *outsocket_,
                        void *sidesocket_, int swap_ids) nogil:
    
    cdef int ids_done
    cdef zmq_msg_t msg
    cdef int rc = zmq_msg_init (&msg)
    cdef zmq_msg_t id_msg
    rc = zmq_msg_init (&id_msg)
    cdef zmq_msg_t side_msg
    rc = zmq_msg_init (&side_msg)
    cdef zmq_msg_t in_msg
    cdef void *in_data = malloc (2)
    memcpy (in_data, "in", 2)
    rc = zmq_msg_init_data (&in_msg, in_data, 2, z_free, NULL)
    
    cdef zmq_msg_t out_msg
    cdef void *out_data = malloc (3)
    memcpy (out_data, "out", 3)
    rc = zmq_msg_init_data (&out_msg, out_data, 3, z_free, NULL)
    # assert (rc == 0)

    cdef int64_t more
    cdef size_t moresz

    cdef zmq_pollitem_t items [3]
    items [0].socket = insocket_
    items [0].fd = 0
    items [0].events = ZMQ_POLLIN
    items [0].revents = 0
    items [1].socket = outsocket_
    items [1].fd = 0
    items [1].events = ZMQ_POLLIN
    items [1].revents = 0
    # items [2].socket = sidesocket_
    # items [2].fd = 0
    # items [2].events = ZMQ_POLLIN
    # items [2].revents = 0

    while (True):

        # //  Wait while there are either requests or replies to process.
        rc = zmq_poll (&items [0], 2, -1)
        ids_done=0
        # assert (rc > 0)

        # //  The algorithm below asumes ratio of request and replies processed
        # //  under full load to be 1:1. Although processing requests replies
        # //  first is tempting it is suspectible to DoS attacks (overloading
        # //  the system with unsolicited replies).
        # 
        # //  Process a request.
        if (items [0].revents & ZMQ_POLLIN):
            rc = zmq_msg_copy(&side_msg, &in_msg)
            rc = zmq_send (sidesocket_, &side_msg, ZMQ_SNDMORE)
            while (True):
                if swap_ids and not ids_done:
                    # recv two ids into msg, id_msg
                    rc = zmq_recv (insocket_, &msg, 0)
                    rc = zmq_recv (insocket_, &id_msg, 0)
                    # send second id (id_msg) first
                    rc = zmq_msg_copy(&side_msg, &id_msg)
                    rc = zmq_send (outsocket_, &id_msg, ZMQ_SNDMORE)
                    rc = zmq_send (sidesocket_, &side_msg,ZMQ_SNDMORE)
                    # send first id (msg) first
                    rc = zmq_msg_copy(&side_msg, &msg)
                    rc = zmq_send (outsocket_, &msg, ZMQ_SNDMORE)
                    rc = zmq_send (sidesocket_, &side_msg,ZMQ_SNDMORE)
                    
                    # only do it once:
                    ids_done = 1

                rc = zmq_recv (insocket_, &msg, 0)
                # assert (rc == 0)

                moresz = sizeof (more)
                rc = zmq_getsockopt (insocket_, ZMQ_RCVMORE, &more, &moresz)
                # assert (rc == 0)
                rc = zmq_msg_copy(&side_msg, &msg)
                if more:
                    rc = zmq_send (outsocket_, &msg, ZMQ_SNDMORE)
                    rc = zmq_send (sidesocket_, &side_msg,ZMQ_SNDMORE)
                else:
                    rc = zmq_send (outsocket_, &msg, 0)
                    rc = zmq_send (sidesocket_, &side_msg,0)
                # assert (rc == 0)

                if (not more):
                    break
        #     }
        # }
        ids_done=0

        # //  Process a reply.
        if (items [1].revents & ZMQ_POLLIN):
            rc = zmq_msg_copy(&side_msg, &out_msg)
            rc = zmq_send (sidesocket_, &side_msg, ZMQ_SNDMORE)
            while (True):
                if swap_ids and not ids_done:
                    # recv two ids into msg, id_msg
                    rc = zmq_recv (outsocket_, &msg, 0)
                    rc = zmq_recv (outsocket_, &id_msg, 0)
                    # send second id (id_msg) first
                    rc = zmq_msg_copy(&side_msg, &id_msg)
                    rc = zmq_send (insocket_, &id_msg, ZMQ_SNDMORE)
                    rc = zmq_send (sidesocket_, &side_msg,ZMQ_SNDMORE)
                    # send first id (msg) first
                    rc = zmq_msg_copy(&side_msg, &msg)
                    rc = zmq_send (insocket_, &msg, ZMQ_SNDMORE)
                    rc = zmq_send (sidesocket_, &side_msg,ZMQ_SNDMORE)
                    
                    # only do it once:
                    ids_done = 1

                rc = zmq_recv (outsocket_, &msg, 0)
                # assert (rc == 0)

                moresz = sizeof (more)
                rc = zmq_getsockopt (outsocket_, ZMQ_RCVMORE, &more, &moresz)
                # assert (rc == 0)
                rc = zmq_msg_copy(&side_msg, &msg)
                if more:
                    rc = zmq_send (insocket_, &msg,ZMQ_SNDMORE)
                    rc = zmq_send (sidesocket_, &side_msg,ZMQ_SNDMORE)
                else:
                    rc = zmq_send (insocket_, &msg,0)
                    rc = zmq_send (sidesocket_, &side_msg,0)
                # errno_assert (rc == 0)

                if (not more):
                    break
    return 0

# def monitored_queue(Socket in_socket,Socket out_socket,Socket mon_socket):
#     """"""
#     cdef void *ins=in_socket.handle
#     cdef void *outs=out_socket.handle
#     cdef void *mons=mon_socket.handle
#     with nogil:
#         sidequeue_(ins, outs, mons)

##### end monitored_queue

import threading
class _DeviceThread(threading.Thread):
    """A wrapped Thread for use in the Device"""
    device = None
    def __init__(self, device):
        threading.Thread.__init__(self)
        self.device = device
        
    def run(self):
        return self.device.run()

cdef class Device:
    """A 0MQ Device.

    Device(device_type, in_socket, out_socket)
    
    Beware, this uses a child thread, but as zmq sockets are not threadsafe,
    if you use the sockets in the main thread after starting the device, 
    odd things might happen. See TSDevice for a threadsafe version

    Parameters
    ----------
    device_type : int
        The 0MQ Device type
    {in|out}_socket : Socket
        ZMQ Sockets for in/out behavior
        
    Attributes
    ----------
    daemon: int
        sets whether the thread should be run as a daemon
        Default is true, because if it is False, the thread will not
        exit unless it is killed

    """
    cdef public int device_type
    cdef public int daemon
    cdef public Socket in_socket
    cdef public Socket out_socket
    
    def __cinit__(self, *args, **kwargs):
        """this is complicated to allow subclassing with different signatures"""
        cdef int i=0
        if isinstance(args[0], int):
            self.device_type = args[0]
            i+=1
        else:
            self.device_type = FORWARDER
        self.in_socket = args[i]
        self.out_socket = args[i+1]
        self.daemon=True
    
    def __init__(self, int device_type, Socket in_socket, Socket out_socket):
        """This is just to force init signature."""
        pass
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef int device_type = self.device_type
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        with nogil:
            rc = zmq_device(device_type, ins, outs)
        return rc
    
    def run(self):
        """The runner method. Do not call me directly, instead call self.start()"""
        return self._run()
    
    def start(self):
        """start the thread"""
        thread = _DeviceThread(self)
        if self.daemon:
            thread.setDaemon(True)
        thread.start()

cdef class MonitoredQueue(Device):
    """A MonitoredQueue 0MQ Device.
    
    mq = MonitoredQueue(in_sock, out_sock, mon_sock)
    
    As far as in_sock and out_sock, this functions exactly the same as
    mq = Device(zmq.QUEUE, in_sock, out_sock)
    
    however, every message relayed through the device is also sent via the mon_sock
    If it comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_sock, but it is not restricted.
    
    For Threadsafe edition, see zmq.TSMonitoredQueue
    
    """
    
    cdef public Socket monitor_socket
    cdef int swap_ids
    
    def __cinit__(self, Socket in_socket, Socket out_socket, Socket monitor_socket, *args, **kwargs):
        self.monitor_socket = monitor_socket
        if in_socket.socket_type == XREP and out_socket.socket_type == XREP:
            self.swap_ids = 1
        else:
            self.swap_ids = 0
        # in_socket/out_socket handled by Device 
    
    def __init__(self, Socket in_socket, Socket out_socket, Socket monitor_socket):
        """This is just to force init signature"""
        Device.__init__(self, QUEUE, in_socket, out_socket)
    #     self.monitor_socket = monitor_socket
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        cdef void *mons = self.monitor_socket.handle
        # cdef int swap_ids
        with nogil:
            rc = monitored_queue_(ins, outs, mons, self.swap_ids)
        return rc

        
cdef class TSDevice:
    """A Threadsafe 0MQ Device.
    It behaves the same as the Device, but creates the sockets as part of the run() command
    
    ThreadsafeDevice(device_type, in_socket_type, out_socket_type)
    
    Similar to Device, but socket types instead of sockets themselves are passed, and
    the sockets are created in the work thread, to avoid issues with thread safety.
    As a result, additional bind_{in|out} and connect_{in|out} methods and setsockopt
    allow users to specify connections for the sockets to be specified
    
    Parameters
    ----------
    device_type : int
        The 0MQ Device type
    {in|out}_type : int
        zmq socket types, to be passed later to context.socket(). e.g. zmq.PUB, zmq.SUB, zmq.REQ.
        If out_type is < 0, then in_socket is used for both in_socket and out_socket.
        
    Methods
    -------
    bind_{in_out}(iface)
        passthrough for {in|out}_socket.bind(iface), to be called in the thread
    connect_{in_out}(iface)
        passthrough for {in|out}_socket.connect(iface), to be called in the thread
    setsockopt_{in_out}(opt,value)
        passthrough for {in|out}_socket.setsockopt(opt, value), to be called in the thread
    
    Attributes
    ----------
    daemon: int
        sets whether the thread should be run as a daemon
        Default is true, because if it is false, the thread will not
        exit unless it is killed
    """
    cdef public int device_type
    cdef public int in_type
    cdef public int out_type
    cdef public int daemon
    cdef Context context
    cdef Socket in_socket
    cdef Socket out_socket
    cdef list in_binds
    cdef list out_binds
    cdef list in_connects
    cdef list out_connects
    cdef list in_sockopts
    cdef list out_sockopts
    
    
    def __cinit__(self, int device_type, int in_type, int out_type, *args, **kwargs):
        self.device_type = device_type
        self.in_type = in_type
        self.out_type = out_type
        self.in_binds = list()
        self.in_connects = list()
        self.in_sockopts = list()
        self.out_binds = list()
        self.out_connects = list()
        self.out_sockopts = list()
        self.daemon = True
    
    def __init__(self, int device_type, int in_type, int out_type):
        """force signature"""
        pass
    
    # def __deallocate__(self):
    #     del self.in_binds
    #     del self.in_connects
    #     del self.in_sockopts
    #     del self.out_binds
    #     del self.out_connects
    #     del self.out_sockopts
    # 
    def bind_in(self,iface):
        """enqueue interface for binding on in_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.in_binds.append(iface)
    
    def connect_in(self, iface):
        """enqueue interface for connecting on in_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.in_connects.append(iface)
    
    def setsockopt_in(self, opt, value):
        """enqueue setsockopt(opt, value) for in_socket
        e.g. setsockopt_out(zmq.SUBSCRIBE, 'controller')"""
        self.in_sockopts.append((opt, value))
    
    def bind_out(self,iface):
        """enqueue interface for binding on out_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.out_binds.append(iface)
    
    def connect_out(self, iface):
        """enqueue interface for connecting on out_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.out_connects.append(iface)
    
    def setsockopt_out(self, opt, value):
        """"enqueue setsockopt(opt, value) for out_socket
        e.g. setsockopt_out(zmq.IDENTITY, 'alice')"""
        self.out_sockopts.append((opt, value))
    
    def _setup_sockets(self):
        ctx = Context()
        self.context = ctx
        
        # create the sockets
        self.in_socket = ctx.socket(self.in_type)
        if self.out_type < 0:
            self.out_socket = self.in_socket
        else:
            self.out_socket = ctx.socket(self.out_type)
        
        # set sockopts (must be done first, in case of zmq.IDENTITY)
        for opt,value in self.in_sockopts:
            self.in_socket.setsockopt(opt, value)
        for opt,value in self.out_sockopts:
            self.out_socket.setsockopt(opt, value)
        
        for iface in self.in_binds:
            self.in_socket.bind(iface)
        for iface in self.out_binds:
            self.out_socket.bind(iface)
        
        for iface in self.in_connects:
            self.in_socket.connect(iface)
        for iface in self.out_connects:
            self.out_socket.connect(iface)
    
    def run(self):
        """The runner method. Do not call me directly, instead call self.start()"""
        self._setup_sockets()
        return self._run()
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef int device_type = self.device_type
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        with nogil:
            rc = zmq_device(device_type, ins, outs)
        return rc
    
    def start(self):
        """start the thread"""
        thread = _DeviceThread(self)
        if self.daemon:
            thread.setDaemon(True)
        thread.start()
        
cdef class TSMonitoredQueue_(TSDevice):
    """Threadsafe edition of MonitoredQueue. See TSDevice for most of the spec.
    This ignores the device_type
    And adds a <method>_mon version of each <method>_{in|out} method, 
    for configuring the monitor socket.
    
    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a QUEUE, 
    except each message is also sent out on the monitor socket.
    
    If a message comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_socket, but it is not restricted.
    
    For a non-threasafe edition to which you can pass actual Sockets,
    see MonitoredQueue
    
    """
    cdef public int mon_type
    cdef Socket mon_socket
    cdef list mon_binds
    cdef list mon_connects
    cdef list mon_sockopts
    cdef int swap_ids
    
    def __cinit__(self, int device_type, int in_type, int out_type, int mon_type, *args, **kwargs):
        self.mon_type = mon_type
        self.mon_binds = list()
        self.mon_connects = list()
        self.mon_sockopts = list()
        if in_type == XREP and out_type == XREP:
            self.swap_ids = 1
        else:
            self.swap_ids = 0
        
    
    def __init__(self, int device_type, int in_type, int out_type, int mon_socket):
        TSDevice.__init__(self, QUEUE, in_type, out_type)
    
    # def __deallocate__(self):
    #     del self.mon_binds
    #     del self.mon_connects
    #     del self.mon_sockopts
    # 
    def bind_mon(self,iface):
        """enqueue interface for binding on mon_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.mon_binds.append(iface)
    
    def connect_mon(self, iface):
        """enqueue interface for connecting on mon_socket
        e.g. tcp://127.0.0.1:10101 or inproc://foo"""
        self.mon_connects.append(iface)
    
    def setsockopt_mon(self, opt, value):
        """"enqueue setsockopt(opt, value) for mon_socket
        e.g. setsockopt_mon(zmq.IDENTITY, 'alice')"""
        self.mon_sockopts.append((opt, value))
    
    def _setup_sockets(self):
        TSDevice._setup_sockets(self)
        ctx = self.context
        self.mon_socket = ctx.socket(self.mon_type)
        
        # set sockopts (must be done first, in case of zmq.IDENTITY)
        for opt,value in self.mon_sockopts:
            self.mon_socket.setsockopt(opt, value)
        
        for iface in self.mon_binds:
            self.mon_socket.bind(iface)
        
        for iface in self.mon_connects:
            self.mon_socket.connect(iface)
    
    cdef int _run(self) nogil:
        cdef int rc = 0
        cdef void *ins = self.in_socket.handle
        cdef void *outs = self.out_socket.handle
        cdef void *mons = self.mon_socket.handle
        with nogil:
            rc = monitored_queue_(ins, outs, mons,self.swap_ids)
        return rc
        
        
    
def TSMonitoredQueue(int in_type, int out_type, int mon_type):
    """Threadsafe edition of MonitoredQueue. See TSDevice for most of the spec.
    This ignores the device_type
    And adds a <method>_mon version of each <method>_{in|out} method, 
    for configuring the monitor socket.
    
    A MonitoredQueue is a 3-socket ZMQ Device that functions just like a QUEUE, 
    except each message is also sent out on the monitor socket.
    
    If a message comes from in_sock, it will be prefixed with 'in'
    If it comes from out_sock, it will be prefixed with 'out'
    
    A PUB socket is perhaps the most logical for the mon_socket, but it is not restricted.
    
    For a non-threasafe edition to which you can pass actual Sockets,
    see MonitoredQueue
    
    """
    return TSMonitoredQueue_(QUEUE, in_type, out_type, mon_type)

__all__ = [
    'Message',
    'Context',
    'Socket',
    # 'Stopwatch',
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
    'STREAMER',
    'FORWARDER',
    'QUEUE',
    '_poll',
    'select',
    'Poller',
    # 'sidequeue',
    'Device',
    'TSDevice',
    'MonitoredQueue',
    'TSMonitoredQueue',
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
]

