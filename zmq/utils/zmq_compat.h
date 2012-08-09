//-----------------------------------------------------------------------------
//  Copyright (c) 2010-2012 Brian Granger, Min Ragan-Kelley
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

#define _missing (PyErr_SetString(PyExc_NotImplementedError, \
"Not available in current zeromq."), -1)

// new in 2.2.0
#ifndef ZMQ_RCVTIMEO
    #define ZMQ_RCVTIMEO (-1)
#endif
#ifndef ZMQ_SNDTIMEO
    #define ZMQ_SNDTIMEO (-1)
#endif

// new in 3.x
#ifndef EAFNOSUPPORT
    #define EAFNOSUPPORT (-1)
#endif
#ifndef EHOSTUNREACH
    #define EHOSTUNREACH (-1)
#endif

#ifndef ZMQ_MAXMSGSIZE
    #define ZMQ_MAXMSGSIZE (-1)
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
#ifndef ZMQ_DONTWAIT
    #define ZMQ_DONTWAIT (-1)
#endif
#ifndef ZMQ_IPV4ONLY
    #define ZMQ_IPV4ONLY (-1)
#endif
#ifndef ZMQ_LAST_ENDPOINT
    #define ZMQ_LAST_ENDPOINT (-1)
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
#ifndef ZMQ_TCP_ACCEPT_FILTER
    #define ZMQ_TCP_ACCEPT_FILTER (-1)
#endif
#ifndef ZMQ_DELAY_ATTACH_ON_CONNECT
    #define ZMQ_DELAY_ATTACH_ON_CONNECT (-1)
#endif

// Message options (3.x)

#ifndef ZMQ_MORE
    #define ZMQ_MORE (-1)
#endif

// Event Monitoring
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


// removed in 3.0.0
#ifndef ZMQ_MAX_VSM_SIZE
    #define ZMQ_MAX_VSM_SIZE (-1)
#endif
#ifndef ZMQ_DELIMITER
    #define ZMQ_DELIMITER (-1)
#endif
#ifndef ZMQ_MSG_MORE
    #define ZMQ_MSG_MORE (-1)
#endif
#ifndef ZMQ_MSG_SHARED
    #define ZMQ_MSG_SHARED (-1)
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

#ifndef ZMQ_NOBLOCK
    #define ZMQ_NOBLOCK (-1)
#endif

// keep the device constants, because we will roll our own zmq_device()
#ifndef ZMQ_STREAMER
    #define ZMQ_STREAMER 1
#endif
#ifndef ZMQ_FORWARDER
    #define ZMQ_FORWARDER 2
#endif
#ifndef ZMQ_QUEUE
    #define ZMQ_QUEUE 3
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
    #define zmq_device(type,in,out) _missing
#else
    #define zmq_sendmsg zmq_send
    #define zmq_recvmsg zmq_recv
    #define zmq_sendbuf (void *s, const void *buf, size_t len, int flags) _missing
    #define zmq_recvbuf (void *s, void *buf, size_t len, int flags) _missing
#endif
