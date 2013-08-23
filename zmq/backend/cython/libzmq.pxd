"""All the C imports for 0MQ"""

#
#    Copyright (c) 2010 Brian E. Granger & Min Ragan-Kelley
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

cdef extern from "zmq_compat.h":
    ctypedef signed long long int64_t "pyzmq_int64_t"

cdef extern from "zmq.h" nogil:

    void _zmq_version "zmq_version"(int *major, int *minor, int *patch)
    
    ctypedef int fd_t "ZMQ_FD_T"
    
    enum: ZMQ_VERSION
    enum: ZMQ_VERSION_MAJOR
    enum: ZMQ_VERSION_MINOR
    enum: ZMQ_VERSION_PATCH
    enum: ZMQ_NOBLOCK
    enum: ZMQ_DONTWAIT
    enum: ZMQ_POLLIN
    enum: ZMQ_POLLOUT
    enum: ZMQ_POLLERR
    enum: ZMQ_SNDMORE
    enum: ZMQ_STREAMER
    enum: ZMQ_FORWARDER
    enum: ZMQ_QUEUE
    enum: ZMQ_PAIR
    enum: ZMQ_PUB
    enum: ZMQ_SUB
    enum: ZMQ_REQ
    enum: ZMQ_REP
    enum: ZMQ_DEALER
    enum: ZMQ_ROUTER
    enum: ZMQ_PULL
    enum: ZMQ_PUSH
    enum: ZMQ_XPUB
    enum: ZMQ_XSUB
    enum: ZMQ_EVENT_CONNECTED
    enum: ZMQ_EVENT_CONNECT_DELAYED
    enum: ZMQ_EVENT_CONNECT_RETRIED
    enum: ZMQ_EVENT_LISTENING
    enum: ZMQ_EVENT_BIND_FAILED
    enum: ZMQ_EVENT_ACCEPTED
    enum: ZMQ_EVENT_ACCEPT_FAILED
    enum: ZMQ_EVENT_CLOSED
    enum: ZMQ_EVENT_CLOSE_FAILED
    enum: ZMQ_EVENT_DISCONNECTED
    enum: ZMQ_EAGAIN "EAGAIN"
    enum: ZMQ_EINVAL "EINVAL"
    enum: ZMQ_EFAULT "EFAULT"
    enum: ZMQ_ENOMEM "ENOMEM"
    enum: ZMQ_ENODEV "ENODEV"
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
    enum: ZMQ_EFSM "EFSM"
    enum: ZMQ_ENOCOMPATPROTO "ENOCOMPATPROTO"
    enum: ZMQ_ETERM "ETERM"
    enum: ZMQ_EMTHREAD "EMTHREAD"
    enum: ZMQ_EAGAIN "EAGAIN"
    enum: ZMQ_EINVAL "EINVAL"
    enum: ZMQ_EFAULT "EFAULT"
    enum: ZMQ_ENOMEM "ENOMEM"
    enum: ZMQ_ENODEV "ENODEV"
    enum: ZMQ_ENOTSUP "ENOTSUP"
    enum: ZMQ_EPROTONOSUPPORT "EPROTONOSUPPORT"
    enum: ZMQ_ENOBUFS "ENOBUFS"
    enum: ZMQ_ENETDOWN "ENETDOWN"
    enum: ZMQ_EADDRINUSE "EADDRINUSE"
    enum: ZMQ_EADDRNOTAVAIL "EADDRNOTAVAIL"
    enum: ZMQ_ECONNREFUSED "ECONNREFUSED"
    enum: ZMQ_EINPROGRESS "EINPROGRESS"
    enum: ZMQ_ENOTSOCK "ENOTSOCK"
    enum: ZMQ_EFSM "EFSM"
    enum: ZMQ_ENOCOMPATPROTO "ENOCOMPATPROTO"
    enum: ZMQ_ETERM "ETERM"
    enum: ZMQ_EMTHREAD "EMTHREAD"
    enum: ZMQ_IO_THREADS
    enum: ZMQ_MAX_SOCKETS
    enum: ZMQ_MORE
    enum: ZMQ_IDENTITY
    enum: ZMQ_SUBSCRIBE
    enum: ZMQ_UNSUBSCRIBE
    enum: ZMQ_LAST_ENDPOINT
    enum: ZMQ_TCP_ACCEPT_FILTER
    enum: ZMQ_RECONNECT_IVL_MAX
    enum: ZMQ_SNDTIMEO
    enum: ZMQ_RCVTIMEO
    enum: ZMQ_SNDHWM
    enum: ZMQ_RCVHWM
    enum: ZMQ_MULTICAST_HOPS
    enum: ZMQ_IPV4ONLY
    enum: ZMQ_ROUTER_BEHAVIOR
    enum: ZMQ_TCP_KEEPALIVE
    enum: ZMQ_TCP_KEEPALIVE_CNT
    enum: ZMQ_TCP_KEEPALIVE_IDLE
    enum: ZMQ_TCP_KEEPALIVE_INTVL
    enum: ZMQ_DELAY_ATTACH_ON_CONNECT
    enum: ZMQ_XPUB_VERBOSE
    enum: ZMQ_ROUTER_RAW
    enum: ZMQ_FD
    enum: ZMQ_EVENTS
    enum: ZMQ_TYPE
    enum: ZMQ_LINGER
    enum: ZMQ_RECONNECT_IVL
    enum: ZMQ_BACKLOG
    enum: ZMQ_AFFINITY
    enum: ZMQ_MAXMSGSIZE
    enum: ZMQ_HWM
    enum: ZMQ_SWAP
    enum: ZMQ_MCAST_LOOP
    enum: ZMQ_RECOVERY_IVL_MSEC
    enum: ZMQ_RATE
    enum: ZMQ_RECOVERY_IVL
    enum: ZMQ_SNDBUF
    enum: ZMQ_RCVBUF
    enum: ZMQ_RCVMORE
    
    enum: errno
    char *zmq_strerror (int errnum)
    int zmq_errno()

    void *zmq_ctx_new ()
    int zmq_ctx_destroy (void *context)
    int zmq_ctx_set (void *context, int option, int optval)
    int zmq_ctx_get (void *context, int option)
    void *zmq_init (int io_threads)
    int zmq_term (void *context)
    
    # blackbox def for zmq_msg_t
    ctypedef void * zmq_msg_t "zmq_msg_t"
    
    ctypedef void zmq_free_fn(void *data, void *hint)
    
    int zmq_msg_init (zmq_msg_t *msg)
    int zmq_msg_init_size (zmq_msg_t *msg, size_t size)
    int zmq_msg_init_data (zmq_msg_t *msg, void *data,
        size_t size, zmq_free_fn *ffn, void *hint)
    int zmq_msg_send (zmq_msg_t *msg, void *s, int flags)
    int zmq_msg_recv (zmq_msg_t *msg, void *s, int flags)
    int zmq_msg_close (zmq_msg_t *msg)
    int zmq_msg_move (zmq_msg_t *dest, zmq_msg_t *src)
    int zmq_msg_copy (zmq_msg_t *dest, zmq_msg_t *src)
    void *zmq_msg_data (zmq_msg_t *msg)
    size_t zmq_msg_size (zmq_msg_t *msg)
    int zmq_msg_more (zmq_msg_t *msg)
    int zmq_msg_get (zmq_msg_t *msg, int option)
    int zmq_msg_set (zmq_msg_t *msg, int option, int optval)

    void *zmq_socket (void *context, int type)
    int zmq_close (void *s)
    int zmq_setsockopt (void *s, int option, void *optval, size_t optvallen)
    int zmq_getsockopt (void *s, int option, void *optval, size_t *optvallen)
    int zmq_bind (void *s, char *addr)
    int zmq_connect (void *s, char *addr)
    int zmq_unbind (void *s, char *addr)
    int zmq_disconnect (void *s, char *addr)
    
    # send/recv
    int zmq_sendbuf (void *s, const_void_ptr buf, size_t n, int flags)
    int zmq_recvbuf (void *s, void *buf, size_t n, int flags)

    ctypedef struct zmq_pollitem_t:
        void *socket
        int fd
        short events
        short revents

    int zmq_poll (zmq_pollitem_t *items, int nitems, long timeout)

    int zmq_device (int device_, void *insocket_, void *outsocket_)
    int zmq_proxy (void *frontend, void *backend, void *capture)

cdef extern from "zmq_utils.h" nogil:

    void *zmq_stopwatch_start ()
    unsigned long zmq_stopwatch_stop (void *watch_)
    void zmq_sleep (int seconds_)

