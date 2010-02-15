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

# Use the fast send and recv that doesn't make copies of data.
_FAST = True

from stdlib cimport *
from python_string cimport PyString_FromStringAndSize
from python_string cimport PyString_AsStringAndSize
from python_string cimport PyString_AsString, PyString_Size
from python_ref cimport Py_DECREF, Py_INCREF

cdef extern from "Python.h":
    ctypedef int Py_ssize_t
    ctypedef int PyGILState_STATE
    PyGILState_STATE    PyGILState_Ensure()
    void                PyGILState_Release(PyGILState_STATE)

import cPickle as pickle

try:
    import json
except ImportError:
    try:
        import simlejson as json
    except ImportError:
        json = None

include "allocate.pxi"

#-----------------------------------------------------------------------------
# Import the C header files
#-----------------------------------------------------------------------------

cdef extern from "errno.h" nogil:
    enum: EINVAL
    enum: EAGAIN

cdef extern from "string.h" nogil:
    void *memcpy(void *dest, void *src, size_t n)
    size_t strlen(char *s)

cdef extern from "zmq.h" nogil:
    enum: ZMQ_HAUSNUMERO
    enum: ENOTSUP
    enum: EPROTONOSUPPORT
    enum: ENOBUFS
    enum: ENETDOWN
    enum: EADDRINUSE
    enum: EADDRNOTAVAIL
    enum: ECONNREFUSED
    enum: EINPROGRESS
    enum: EMTHREAD
    enum: EFSM
    enum: ENOCOMPATPROTO

    enum: errno
    char *zmq_strerror (int errnum)

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
    
    enum: ZMQ_POLL # 1

    void *zmq_init (int app_threads, int io_threads, int flags)
    int zmq_term (void *context)

    enum: ZMQ_P2P # 0
    enum: ZMQ_PUB # 1
    enum: ZMQ_SUB # 2
    enum: ZMQ_REQ # 3
    enum: ZMQ_REP # 4
    enum: ZMQ_XREQ # 5
    enum: ZMQ_XREP # 6
    enum: ZMQ_UPSTREAM # 7
    enum: ZMQ_DOWNSTREAM # 8

    enum: ZMQ_HWM # 1
    enum: ZMQ_LWM # 2
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

    enum: ZMQ_NOBLOCK # 1
    enum: ZMQ_NOFLUSH # 2

    void *zmq_socket (void *context, int type)
    int zmq_close (void *s)
    int zmq_setsockopt (void *s, int option, void *optval, size_t optvallen)
    int zmq_bind (void *s, char *addr)
    int zmq_connect (void *s, char *addr)
    int zmq_send (void *s, zmq_msg_t *msg, int flags)
    int zmq_flush (void *s)
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

    int zmq_poll (zmq_pollitem_t *items, int nitems, long timeout)

    void *zmq_stopwatch_start ()
    unsigned long zmq_stopwatch_stop (void *watch_)
    void zmq_sleep (int seconds_)

#-----------------------------------------------------------------------------
# Python module level constants
#-----------------------------------------------------------------------------

NOBLOCK = ZMQ_NOBLOCK
NOFLUSH = ZMQ_NOFLUSH
P2P = ZMQ_P2P
PUB = ZMQ_PUB
SUB = ZMQ_SUB
REQ = ZMQ_REQ
REP = ZMQ_REP
XREQ = ZMQ_XREQ
XREP = ZMQ_XREP
UPSTREAM = ZMQ_UPSTREAM
DOWNSTREAM = ZMQ_DOWNSTREAM
HWM = ZMQ_HWM
LWM = ZMQ_LWM
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
POLL = ZMQ_POLL
POLLIN = ZMQ_POLLIN
POLLOUT = ZMQ_POLLOUT
POLLERR = ZMQ_POLLERR

#-----------------------------------------------------------------------------
# Error handling
#-----------------------------------------------------------------------------

def strerror(errnum):
    """Return the error string given the error number."""
    return zmq_strerror(errnum)

class ZMQError(Exception):
    """Base exception class for ZMQ errors in Python."""
    pass

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

cdef class Context:
    """Manage the lifecycle of a ZMQ context."""

    cdef void *handle

    def __cinit__(self, int app_threads=1, int io_threads=1, int flags=0):
        self.handle = NULL
        self.handle = zmq_init(app_threads, io_threads, flags)
        if self.handle == NULL:
            raise ZMQError(zmq_strerror(errno))

    def __dealloc__(self):
        cdef int rc
        if self.handle != NULL:
            rc = zmq_term(self.handle)
            if rc != 0:
                raise ZMQError(zmq_strerror(errno))


cdef void free_python_msg(void *data, void *hint) with gil:
    """A function for DECREF'ing Python based messages."""
    if hint != NULL:
        Py_DECREF(<object>hint)


cdef class Socket:
    """Manage the lifecycle of the ZMQ socket."""

    cdef void *handle
    cdef public int socket_type
    # Hold on to a reference to the context to make sure it is not garbage
    # collected until the socket it done with it.
    cdef public Context context

    def __cinit__(self, Context context, int socket_type):
        self.handle = NULL
        self.context = context
        self.socket_type = socket_type
        self.handle = zmq_socket(context.handle, socket_type)
        if self.handle == NULL:
            raise ZMQError(zmq_strerror(errno))

    def __dealloc__(self):
        cdef int rc
        if self.handle != NULL:
            rc = zmq_close(self.handle)
            if rc != 0:
                raise ZMQError(zmq_strerror(errno))

    def setsockopt(self, option, optval):
        cdef int optval_int_c
        cdef int rc

        if not isinstance(option, int):
            raise TypeError('expected int, got: %r' % option)

        if option in [SUBSCRIBE, UNSUBSCRIBE, IDENTITY]:
            if not isinstance(optval, str):
                raise TypeError('expected str, got: %r' % optval)
            opt_val_str_c = optval
            rc = zmq_setsockopt(
                self.handle, option,
                PyString_AsString(optval), PyString_Size(optval)
            )
        elif option in [HWM, LWM, SWAP, AFFINITY, RATE, RECOVERY_IVL,
                        MCAST_LOOP, SNDBUF, RCVBUF]:
            if not isinstance(optval, int):
                raise TypeError('expected int, got: %r' % optval)
            optval_int_c = optval
            rc = zmq_setsockopt(
                self.handle, option,
                &optval_int_c, sizeof(int)
            )
        else:
            rc = -1
            errno = EINVAL

        if rc != 0:
            raise ZMQError(zmq_strerror(errno))

    def bind(self, addr):
        cdef int rc
        if not isinstance(addr, str):
            raise TypeError('expected str, got: %r' % addr)
        rc = zmq_bind(self.handle, addr)
        if rc != 0:
            raise ZMQError(zmq_strerror(errno))

    def connect(self, addr):
        cdef int rc
        if not isinstance(addr, str):
            raise TypeError('expected str, got: %r' % addr)
        rc = zmq_connect(self.handle, addr)
        if rc != 0:
            raise ZMQError(zmq_strerror(errno))

    def flush(self):
        cdef int rc
        rc = zmq_flush(self.handle)
        if rc != 0:
            raise ZMQError(zmq_strerror(errno))

    def send(self, msg, flags=0):
        cdef int rc, rc2
        cdef zmq_msg_t data
        cdef char *msg_c
        cdef Py_ssize_t msg_c_len

        if not isinstance(msg, str):
            raise TypeError('expected str, got: %r' % msg)
        if not isinstance(flags, int):
            raise TypeError('expected str, got: %r' % msg)

        # If zmq_msg_init_* fails do we need to call zmq_msg_close?

        PyString_AsStringAndSize(msg, &msg_c, &msg_c_len)
        # Copy the msg before sending. This avoids any complications with
        # the GIL, etc.
        rc = zmq_msg_init_size(&data, msg_c_len)
        memcpy(zmq_msg_data(&data), msg_c, zmq_msg_size(&data))

        if rc != 0:
            raise ZMQError(zmq_strerror(errno))

        with nogil:
            rc = zmq_send(self.handle, &data, flags)
        rc2 = zmq_msg_close(&data)

        # Shouldn't the error handling for zmq_msg_close come after that
        # of zmq_send?
        if rc2 != 0:
            raise ZMQError(zmq_strerror(errno))

        if rc != 0:
            if errno == EAGAIN:
                return False
            else:
                if rc != 0:
                    raise ZMQError(zmq_strerror(errno))
        else:
            return True

    def recv(self, flags=0):
        cdef int rc
        cdef zmq_msg_t data
        # cdef char *msg_c

        if not isinstance(flags, int):
            raise TypeError('expected str, got: %r' % msg)

        rc = zmq_msg_init(&data)
        if rc != 0:
            raise ZMQError(zmq_strerror(errno))

        with nogil:
            rc = zmq_recv(self.handle, &data, flags)

        if rc != 0:
            if errno == EAGAIN:
                return None
            if rc != 0:
                raise ZMQError(zmq_strerror(errno))

        msg = PyString_FromStringAndSize(
            <char *>zmq_msg_data(&data), 
            zmq_msg_size(&data)
        )

        rc = zmq_msg_close(&data)
        if rc != 0:
            raise ZMQError(zmq_strerror(errno))
        return msg

    def send_pyobj(self, obj, flags=0):
        msg = pickle.dumps(obj, 2)
        return self.send(msg, flags)

    def recv_pyobj(self, flags=0):
        s = self.recv(flags)
        return pickle.loads(s)

    def send_json(self, obj, flags=0):
        if json is None:
            raise ImportError('json or simplejson library is required.')
        else:
            msg = json.dumps(obj, separators=(',',':'))
            return self.send(msg, flags)

    def recv_json(self, flags=0):
        if json is None:
            raise ImportError('json or simplejson library is required.')
        else:
            s = self.recv(flags)
            return json.loads(s)

cdef class Stopwatch:
    """A simple stopwatch based on zmq_stopwatch_start/stop."""

    cdef void *watch

    def __cinit__(self):
        self.watch = NULL

    def start(self):
        if self.watch == NULL:
            self.watch = zmq_stopwatch_start()
        else:
            raise ZMQError('Stopwatch is already runing.')

    def stop(self):
        if self.watch == NULL:
            raise ZMQError('Must start the Stopwatch before calling stop.')
        else:
            time = zmq_stopwatch_stop(self.watch)
            self.watch = NULL
            return time

    def clear(self):
        self.watch = NULL

    def sleep(self, int seconds):
        zmq_sleep(seconds)


def poll(sockets, long timeout=2):
    """Poll a set of 0MQ sockets."""
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
        else:
            raise NotImplementedError('This only works for ZMQ sockets.')

    rc = zmq_poll(pollitems, nsockets, timeout)
    if rc != 0:
        raise ZMQError(zmq_strerror(errno))
    
    results = []
    for i in range(nsockets):
        results.append((sockets[i][0], pollitems[i].revents))

    return results


__all__ = [
    'Context',
    'Socket',
    'ZMQError',
    'Stopwatch',
    'NOBLOCK',
    'NOFLUSH',
    'P2P',
    'PUB',
    'SUB',
    'REQ',
    'REP',
    'XREQ',
    'XREP',
    'UPSTREAM',
    'DOWNSTREAM',
    'HWM',
    'LWM',
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
    'POLL',
    'POLLIN',
    'POLLOUT',
    'poll'
]