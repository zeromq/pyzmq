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


#include "zmq.h"
// version compatibility for constants:
#include "zmq_constants.h"

#define _missing (-1)


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

#if ZMQ_VERSION_MAJOR >= 4
// nothing to remove
#else
    #define zmq_curve_keypair(z85_public_key, z85_secret_key) _missing
#endif

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

    #define zmq_socket_monitor(s, addr, flags) _missing

#endif
