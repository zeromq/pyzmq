#if defined(_MSC_VER)
#define pyzmq_int64_t __int64
#else
#include <stdint.h>
#define pyzmq_int64_t int64_t
#endif

// version compatibility for constants:
#include "zmq.h"
#define _missing (PyErr_SetString(PyExc_NotImplementedError, \
                "Constant not available in current zeromq."), -1)
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
