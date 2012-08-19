"""All the C imports for 0MQ"""

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

#-----------------------------------------------------------------------------
# Import the C header files
#-----------------------------------------------------------------------------

cdef extern from *:
    ctypedef void* const_void_ptr "const void *"

cdef extern from "allocate.h":
    object allocate(size_t n, void **pp)

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
    
    ctypedef int fd_t "ZMQ_FD_T"
    
    enum: ZMQ_VERSION_MAJOR
    enum: ZMQ_VERSION_MINOR
    enum: ZMQ_VERSION_PATCH
    enum: ZMQ_VERSION

    enum: ZMQ_HAUSNUMERO
    enum: ZMQ_ENOTSUP "ENOTSUP"
    enum: ZMQ_EPROTONOSUPPORT "EPROTONOSUPPORT"
    enum: ZMQ_ENOBUFS "ENOBUFS"
    enum: ZMQ_ENETDOWN "ENETDOWN"
    enum: ZMQ_EADDRINUSE "EADDRINUSE"
    enum: ZMQ_EADDRNOTAVAIL "EADDRNOTAVAIL"
    enum: ZMQ_ECONNREFUSED "ECONNREFUSED"
    enum: ZMQ_EINPROGRESS "EINPROGRESS"
    enum: ZMQ_ENOTSOCK "ENOTSOCK"
    enum: ZMQ_EAFNOSUPPORT "EAFNOSUPPORT"
    enum: ZMQ_EHOSTUNREACH "EHOSTUNREACH"

    enum: ZMQ_EFSM "EFSM"
    enum: ZMQ_ENOCOMPATPROTO "ENOCOMPATPROTO"
    enum: ZMQ_ETERM "ETERM"
    enum: ZMQ_EMTHREAD "EMTHREAD"
    
    enum: errno
    char *zmq_strerror (int errnum)
    int zmq_errno()

    enum: ZMQ_MAX_VSM_SIZE # 30
    enum: ZMQ_DELIMITER # 31
    enum: ZMQ_VSM # 32
    enum: ZMQ_MSG_MORE # 1
    enum: ZMQ_MSG_SHARED # 128
    
    # blackbox def for zmq_msg_t
    ctypedef void * zmq_msg_t "zmq_msg_t"
    
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
    enum: ZMQ_DEALER # 5
    enum: ZMQ_ROUTER # 6
    enum: ZMQ_PULL # 7
    enum: ZMQ_PUSH # 8
    enum: ZMQ_XPUB # 9
    enum: ZMQ_XSUB # 10

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
    enum: ZMQ_FD # 14
    enum: ZMQ_EVENTS # 15
    enum: ZMQ_TYPE # 16
    enum: ZMQ_LINGER # 17
    enum: ZMQ_RECONNECT_IVL # 18
    enum: ZMQ_BACKLOG # 19
    enum: ZMQ_RECOVERY_IVL_MSEC # 20
    enum: ZMQ_RECONNECT_IVL_MAX # 21
    enum: ZMQ_MAXMSGSIZE # 22
    enum: ZMQ_SNDHWM # 23
    enum: ZMQ_RCVHWM # 24
    enum: ZMQ_MULTICAST_HOPS # 25
    enum: ZMQ_RCVTIMEO # 27
    enum: ZMQ_SNDTIMEO # 28
    enum: ZMQ_IPV4ONLY # 31
    enum: ZMQ_LAST_ENDPOINT # 32

    enum: ZMQ_ROUTER_BEHAVIOR # 33
    enum: ZMQ_TCP_KEEPALIVE # 34
    enum: ZMQ_TCP_KEEPALIVE_CNT # 35
    enum: ZMQ_TCP_KEEPALIVE_IDLE # 36
    enum: ZMQ_TCP_KEEPALIVE_INTVL # 37
    enum: ZMQ_TCP_ACCEPT_FILTER # 38
    enum: ZMQ_DELAY_ATTACH_ON_CONNECT # 39

    enum: ZMQ_MORE # 1

    enum: ZMQ_NOBLOCK # 1
    enum: ZMQ_DONTWAIT # 1
    enum: ZMQ_SNDMORE # 2

    # Socket transport events (tcp and ipc only)
    enum: ZMQ_EVENT_CONNECTED # 1
    enum: ZMQ_EVENT_CONNECT_DELAYED # 2
    enum: ZMQ_EVENT_CONNECT_RETRIED # 4

    enum: ZMQ_EVENT_LISTENING # 8
    enum: ZMQ_EVENT_BIND_FAILED # 16

    enum: ZMQ_EVENT_ACCEPTED # 32
    enum: ZMQ_EVENT_ACCEPT_FAILED # 64

    enum: ZMQ_EVENT_CLOSED # 128
    enum: ZMQ_EVENT_CLOSE_FAILED # 256
    enum: ZMQ_EVENT_DISCONNECTED # 512

    void *zmq_socket (void *context, int type)
    int zmq_close (void *s)
    int zmq_setsockopt (void *s, int option, void *optval, size_t optvallen)
    int zmq_getsockopt (void *s, int option, void *optval, size_t *optvallen)
    int zmq_bind (void *s, char *addr)
    int zmq_connect (void *s, char *addr)
    # send/recv
    int zmq_sendmsg (void *s, zmq_msg_t *msg, int flags)
    int zmq_recvmsg (void *s, zmq_msg_t *msg, int flags)
    int zmq_sendbuf (void *s, const_void_ptr buf, size_t n, int flags)
    int zmq_recvbuf (void *s, void *buf, size_t n, int flags)

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

    enum: ZMQ_STREAMER
    enum: ZMQ_FORWARDER
    enum: ZMQ_QUEUE
    # removed in libzmq
    int zmq_device (int device_, void *insocket_, void *outsocket_)

cdef extern from "zmq_utils.h" nogil:

    void *zmq_stopwatch_start ()
    unsigned long zmq_stopwatch_stop (void *watch_)
    void zmq_sleep (int seconds_)

