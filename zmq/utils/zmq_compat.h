//-----------------------------------------------------------------------------
//  Copyright (c) 2010 Brian Granger, Min Ragan-Kelley
//
//  Distributed under the terms of the New BSD License.  The full license is in
//  the file COPYING.BSD, distributed as part of this software.
//-----------------------------------------------------------------------------

#if defined(_MSC_VER)
#define pyzmq_int64_t __int64
#else
#include <stdint.h>
#define pyzmq_int64_t int64_t
#endif


// version compatibility for constants:
#include "zmq.h"

#define _missing (-1)

#ifndef ZMQ_VERSION
    #define ZMQ_VERSION (-1)
#endif

#ifndef ZMQ_VERSION_MAJOR
    #define ZMQ_VERSION_MAJOR (-1)
#endif

#ifndef ZMQ_VERSION_MINOR
    #define ZMQ_VERSION_MINOR (-1)
#endif

#ifndef ZMQ_VERSION_PATCH
    #define ZMQ_VERSION_PATCH (-1)
#endif

#ifndef ZMQ_NOBLOCK
    #define ZMQ_NOBLOCK (-1)
#endif

#ifndef ZMQ_DONTWAIT
    #define ZMQ_DONTWAIT (-1)
#endif

#ifndef ZMQ_POLLIN
    #define ZMQ_POLLIN (-1)
#endif

#ifndef ZMQ_POLLOUT
    #define ZMQ_POLLOUT (-1)
#endif

#ifndef ZMQ_POLLERR
    #define ZMQ_POLLERR (-1)
#endif

#ifndef ZMQ_SNDMORE
    #define ZMQ_SNDMORE (-1)
#endif

#ifndef ZMQ_STREAMER
    #define ZMQ_STREAMER (-1)
#endif

#ifndef ZMQ_FORWARDER
    #define ZMQ_FORWARDER (-1)
#endif

#ifndef ZMQ_QUEUE
    #define ZMQ_QUEUE (-1)
#endif

#ifndef ZMQ_IO_THREADS_DFLT
    #define ZMQ_IO_THREADS_DFLT (-1)
#endif

#ifndef ZMQ_MAX_SOCKETS_DFLT
    #define ZMQ_MAX_SOCKETS_DFLT (-1)
#endif

#ifndef ZMQ_PAIR
    #define ZMQ_PAIR (-1)
#endif

#ifndef ZMQ_PUB
    #define ZMQ_PUB (-1)
#endif

#ifndef ZMQ_SUB
    #define ZMQ_SUB (-1)
#endif

#ifndef ZMQ_REQ
    #define ZMQ_REQ (-1)
#endif

#ifndef ZMQ_REP
    #define ZMQ_REP (-1)
#endif

#ifndef ZMQ_DEALER
    #define ZMQ_DEALER (-1)
#endif

#ifndef ZMQ_ROUTER
    #define ZMQ_ROUTER (-1)
#endif

#ifndef ZMQ_PULL
    #define ZMQ_PULL (-1)
#endif

#ifndef ZMQ_PUSH
    #define ZMQ_PUSH (-1)
#endif

#ifndef ZMQ_XPUB
    #define ZMQ_XPUB (-1)
#endif

#ifndef ZMQ_XSUB
    #define ZMQ_XSUB (-1)
#endif

#ifndef ZMQ_UPSTREAM
    #define ZMQ_UPSTREAM (-1)
#endif

#ifndef ZMQ_DOWNSTREAM
    #define ZMQ_DOWNSTREAM (-1)
#endif

#ifndef ZMQ_EVENT_CONNECTED
    #define ZMQ_EVENT_CONNECTED (-1)
#endif

#ifndef ZMQ_EVENT_CONNECT_DELAYED
    #define ZMQ_EVENT_CONNECT_DELAYED (-1)
#endif

#ifndef ZMQ_EVENT_CONNECT_RETRIED
    #define ZMQ_EVENT_CONNECT_RETRIED (-1)
#endif

#ifndef ZMQ_EVENT_LISTENING
    #define ZMQ_EVENT_LISTENING (-1)
#endif

#ifndef ZMQ_EVENT_BIND_FAILED
    #define ZMQ_EVENT_BIND_FAILED (-1)
#endif

#ifndef ZMQ_EVENT_ACCEPTED
    #define ZMQ_EVENT_ACCEPTED (-1)
#endif

#ifndef ZMQ_EVENT_ACCEPT_FAILED
    #define ZMQ_EVENT_ACCEPT_FAILED (-1)
#endif

#ifndef ZMQ_EVENT_CLOSED
    #define ZMQ_EVENT_CLOSED (-1)
#endif

#ifndef ZMQ_EVENT_CLOSE_FAILED
    #define ZMQ_EVENT_CLOSE_FAILED (-1)
#endif

#ifndef ZMQ_EVENT_DISCONNECTED
    #define ZMQ_EVENT_DISCONNECTED (-1)
#endif

#ifndef ZMQ_EVENT_ALL
    #define ZMQ_EVENT_ALL (-1)
#endif

#ifndef EAGAIN
    #define EAGAIN (-1)
#endif

#ifndef EINVAL
    #define EINVAL (-1)
#endif

#ifndef EFAULT
    #define EFAULT (-1)
#endif

#ifndef ENOMEM
    #define ENOMEM (-1)
#endif

#ifndef ENODEV
    #define ENODEV (-1)
#endif

#ifndef EMSGSIZE
    #define EMSGSIZE (-1)
#endif

#ifndef EAFNOSUPPORT
    #define EAFNOSUPPORT (-1)
#endif

#ifndef ENETUNREACH
    #define ENETUNREACH (-1)
#endif

#ifndef ECONNABORTED
    #define ECONNABORTED (-1)
#endif

#ifndef ECONNRESET
    #define ECONNRESET (-1)
#endif

#ifndef ENOTCONN
    #define ENOTCONN (-1)
#endif

#ifndef ETIMEDOUT
    #define ETIMEDOUT (-1)
#endif

#ifndef EHOSTUNREACH
    #define EHOSTUNREACH (-1)
#endif

#ifndef ENETRESET
    #define ENETRESET (-1)
#endif

#ifndef ZMQ_HAUSNUMERO
    #define ZMQ_HAUSNUMERO (-1)
#endif

#ifndef ENOTSUP
    #define ENOTSUP (-1)
#endif

#ifndef EPROTONOSUPPORT
    #define EPROTONOSUPPORT (-1)
#endif

#ifndef ENOBUFS
    #define ENOBUFS (-1)
#endif

#ifndef ENETDOWN
    #define ENETDOWN (-1)
#endif

#ifndef EADDRINUSE
    #define EADDRINUSE (-1)
#endif

#ifndef EADDRNOTAVAIL
    #define EADDRNOTAVAIL (-1)
#endif

#ifndef ECONNREFUSED
    #define ECONNREFUSED (-1)
#endif

#ifndef EINPROGRESS
    #define EINPROGRESS (-1)
#endif

#ifndef ENOTSOCK
    #define ENOTSOCK (-1)
#endif

#ifndef EFSM
    #define EFSM (-1)
#endif

#ifndef ENOCOMPATPROTO
    #define ENOCOMPATPROTO (-1)
#endif

#ifndef ETERM
    #define ETERM (-1)
#endif

#ifndef EMTHREAD
    #define EMTHREAD (-1)
#endif

#ifndef ZMQ_IO_THREADS
    #define ZMQ_IO_THREADS (-1)
#endif

#ifndef ZMQ_MAX_SOCKETS
    #define ZMQ_MAX_SOCKETS (-1)
#endif

#ifndef ZMQ_MORE
    #define ZMQ_MORE (-1)
#endif

#ifndef ZMQ_IDENTITY
    #define ZMQ_IDENTITY (-1)
#endif

#ifndef ZMQ_SUBSCRIBE
    #define ZMQ_SUBSCRIBE (-1)
#endif

#ifndef ZMQ_UNSUBSCRIBE
    #define ZMQ_UNSUBSCRIBE (-1)
#endif

#ifndef ZMQ_LAST_ENDPOINT
    #define ZMQ_LAST_ENDPOINT (-1)
#endif

#ifndef ZMQ_TCP_ACCEPT_FILTER
    #define ZMQ_TCP_ACCEPT_FILTER (-1)
#endif

#ifndef ZMQ_RECONNECT_IVL_MAX
    #define ZMQ_RECONNECT_IVL_MAX (-1)
#endif

#ifndef ZMQ_SNDTIMEO
    #define ZMQ_SNDTIMEO (-1)
#endif

#ifndef ZMQ_RCVTIMEO
    #define ZMQ_RCVTIMEO (-1)
#endif

#ifndef ZMQ_SNDHWM
    #define ZMQ_SNDHWM (-1)
#endif

#ifndef ZMQ_RCVHWM
    #define ZMQ_RCVHWM (-1)
#endif

#ifndef ZMQ_MULTICAST_HOPS
    #define ZMQ_MULTICAST_HOPS (-1)
#endif

#ifndef ZMQ_IPV4ONLY
    #define ZMQ_IPV4ONLY (-1)
#endif

#ifndef ZMQ_ROUTER_BEHAVIOR
    #define ZMQ_ROUTER_BEHAVIOR (-1)
#endif

#ifndef ZMQ_TCP_KEEPALIVE
    #define ZMQ_TCP_KEEPALIVE (-1)
#endif

#ifndef ZMQ_TCP_KEEPALIVE_CNT
    #define ZMQ_TCP_KEEPALIVE_CNT (-1)
#endif

#ifndef ZMQ_TCP_KEEPALIVE_IDLE
    #define ZMQ_TCP_KEEPALIVE_IDLE (-1)
#endif

#ifndef ZMQ_TCP_KEEPALIVE_INTVL
    #define ZMQ_TCP_KEEPALIVE_INTVL (-1)
#endif

#ifndef ZMQ_DELAY_ATTACH_ON_CONNECT
    #define ZMQ_DELAY_ATTACH_ON_CONNECT (-1)
#endif

#ifndef ZMQ_XPUB_VERBOSE
    #define ZMQ_XPUB_VERBOSE (-1)
#endif

#ifndef ZMQ_ROUTER_RAW
    #define ZMQ_ROUTER_RAW (-1)
#endif

#ifndef ZMQ_FD
    #define ZMQ_FD (-1)
#endif

#ifndef ZMQ_EVENTS
    #define ZMQ_EVENTS (-1)
#endif

#ifndef ZMQ_TYPE
    #define ZMQ_TYPE (-1)
#endif

#ifndef ZMQ_LINGER
    #define ZMQ_LINGER (-1)
#endif

#ifndef ZMQ_RECONNECT_IVL
    #define ZMQ_RECONNECT_IVL (-1)
#endif

#ifndef ZMQ_BACKLOG
    #define ZMQ_BACKLOG (-1)
#endif

#ifndef ZMQ_ROUTER_MANDATORY
    #define ZMQ_ROUTER_MANDATORY (-1)
#endif

#ifndef ZMQ_FAIL_UNROUTABLE
    #define ZMQ_FAIL_UNROUTABLE (-1)
#endif

#ifndef ZMQ_AFFINITY
    #define ZMQ_AFFINITY (-1)
#endif

#ifndef ZMQ_MAXMSGSIZE
    #define ZMQ_MAXMSGSIZE (-1)
#endif

#ifndef ZMQ_HWM
    #define ZMQ_HWM (-1)
#endif

#ifndef ZMQ_SWAP
    #define ZMQ_SWAP (-1)
#endif

#ifndef ZMQ_MCAST_LOOP
    #define ZMQ_MCAST_LOOP (-1)
#endif

#ifndef ZMQ_RECOVERY_IVL_MSEC
    #define ZMQ_RECOVERY_IVL_MSEC (-1)
#endif

#ifndef ZMQ_RATE
    #define ZMQ_RATE (-1)
#endif

#ifndef ZMQ_RECOVERY_IVL
    #define ZMQ_RECOVERY_IVL (-1)
#endif

#ifndef ZMQ_SNDBUF
    #define ZMQ_SNDBUF (-1)
#endif

#ifndef ZMQ_RCVBUF
    #define ZMQ_RCVBUF (-1)
#endif

#ifndef ZMQ_RCVMORE
    #define ZMQ_RCVMORE (-1)
#endif


// define fd type (from libzmq's fd.hpp)
#ifdef _WIN32
  #ifdef _MSC_VER && _MSC_VER <= 1400
    #define ZMQ_FD_T UINT_PTR
  #else
    #define ZMQ_FD_T SOCKET
  #endif
#else
    #define ZMQ_FD_T int
#endif

// use unambiguous aliases for zmq_send/recv functions

#if ZMQ_VERSION_MAJOR >= 3
    #define zmq_sendbuf zmq_send
    #define zmq_recvbuf zmq_recv

    // 3.x deprecations - these symbols haven't been removed,
    // but let's protect against their planned removal
    #define zmq_device(device_type, isocket, osocket) _missing
    #define zmq_init(io_threads) ((void*)NULL)
    #define zmq_term zmq_ctx_destroy
#else
    #define zmq_ctx_set(ctx, opt, val) _missing
    #define zmq_ctx_get(ctx, opt) _missing
    #define zmq_ctx_destroy zmq_term
    #define zmq_ctx_new() ((void*)NULL)

    #define zmq_proxy(a,b,c) _missing

    #define zmq_disconnect(s, addr) _missing
    #define zmq_unbind(s, addr) _missing
    
    #define zmq_msg_more(msg) _missing
    #define zmq_msg_get(msg, opt) _missing
    #define zmq_msg_set(msg, opt, val) _missing
    #define zmq_msg_send(msg, s, flags) zmq_send(s, msg, flags)
    #define zmq_msg_recv(msg, s, flags) zmq_recv(s, msg, flags)
    
    #define zmq_sendbuf(s, buf, len, flags) _missing
    #define zmq_recvbuf(s, buf, len, flags) _missing
#endif
