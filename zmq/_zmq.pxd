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


# from libc.stdlib cimport free,malloc
from cpython cimport bool

#-----------------------------------------------------------------------------
# Import the C header files
#-----------------------------------------------------------------------------

cdef extern from "errno.h" nogil:
    enum: ZMQ_EINVAL "EINVAL"
    enum: ZMQ_EAGAIN "EAGAIN"
    enum: ZMQ_EFAULT "EFAULT"
    enum: ZMQ_ENOMEM "ENOMEM"
    enum: ZMQ_ENODEV "ENODEV"

cdef extern from "string.h" nogil:
    void *memcpy(void *dest, void *src, size_t n)
    size_t strlen(char *s)

cdef extern from "zmq_compat.h":
    ctypedef signed long long int64_t "pyzmq_int64_t"

cdef extern from "zmq.h" nogil:

    void _zmq_version "zmq_version"(int *major, int *minor, int *patch)

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
    enum: ZMQ_MSG_MORE # 1
    enum: ZMQ_MSG_SHARED # 128

    ctypedef struct zmq_msg_t:
        void *content
        unsigned char flags
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
    enum: ZMQ_PULL # 7
    enum: ZMQ_PUSH # 8
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

    int zmq_poll (zmq_pollitem_t *items, int nitems, long timeout)

    enum: ZMQ_STREAMER #1
    enum: ZMQ_FORWARDER #2
    enum: ZMQ_QUEUE #3
    int zmq_device (int device_, void *insocket_, void *outsocket_)

cdef extern from "zmq_utils.h" nogil:

    void *zmq_stopwatch_start ()
    unsigned long zmq_stopwatch_stop (void *watch_)
    void zmq_sleep (int seconds_)


#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

cdef class MessageTracker(object):
    """The MessageTracker object tracks whether a 
    
    It can be constructed from any number of Messages, Queues, 
    or other MessageTracker objects.
    
    socket.send( ... copy=False) returns a MessageTracker object
    """
    
    cdef set queues
    cdef set peers
    

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
    cdef object _data # the actual message data
    cdef object _buffer # a Python Buffer/View of the message contents
    cdef object _bytes # a bytes/str representation of a message; always copied
    cdef bool _failed_init
    # Queues for tracking zmq ref counting, for use in 
    # cdef public object zmq_refcount
    cdef public object send_pending
    cdef public object tracker
    
    cdef Message fast_copy(self)
    cdef object _getbuffer(self)
    cdef object _copybytes(self)
    
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
    cdef public object closed

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

    cdef void *handle
    cdef public int socket_type
    # Hold on to a reference to the context to make sure it is not garbage
    # collected until the socket it done with it.
    cdef public Context context
    cdef public object closed


cdef class Stopwatch:
    """A simple stopwatch based on zmq_stopwatch_start/stop."""

    cdef void *watch



