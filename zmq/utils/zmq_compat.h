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

// 2.1.0

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
// 2.1.1
#ifndef ZMQ_XPUB
    #define ZMQ_XPUB (-1)
#endif
#ifndef ZMQ_XSUB
    #define ZMQ_XSUB (-1)
#endif
#ifndef ZMQ_RECOVERY_IVL_MSEC
    #define ZMQ_RECOVERY_IVL_MSEC (-1)
#endif
#ifndef ZMQ_RECONNECT_IVL_MAX
    #define ZMQ_RECONNECT_IVL_MAX (-1)
#endif
// 2.1.4
#ifndef ZMQ_DEALER
    #define ZMQ_DEALER (-1)
#endif
#ifndef ZMQ_ROUTER
    #define ZMQ_ROUTER (-1)
#endif

// new in 3.0.0
#ifndef ENOTSOCK
    #define ENOTSOCK (-1)
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

#ifndef ZMQ_DONTWAIT
    #define ZMQ_DONTWAIT (-1)
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

#ifndef ZMQ_UPSTREAM
    #define ZMQ_UPSTREAM (-1)
#endif
#ifndef ZMQ_DOWNSTREAM
    #define ZMQ_DOWNSTREAM (-1)
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
