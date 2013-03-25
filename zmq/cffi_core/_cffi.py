# coding: utf-8
"""The main CFFI wrapping of libzmq"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from cffi import FFI

ffi = FFI()

errnos =  ['EADDRINUSE', 'EADDRNOTAVAIL', 'EAGAIN', 'ECONNREFUSED', 'EFAULT',
           'EFSM', 'EINPROGRESS', 'EINVAL', 'EMTHREAD', 'ENETDOWN', 'ENOBUFS',
           'ENOCOMPATPROTO', 'ENODEV', 'ENOMEM', 'ENOTSUP', 'EPROTONOSUPPORT',
           'ETERM', 'ENOTSOCK', 'EMSGSIZE', 'EAFNOSUPPORT', 'ENETUNREACH',
           'ECONNABORTED', 'ECONNRESET', 'ENOTCONN', 'ETIMEDOUT',
           'EHOSTUNREACH', 'ENETRESET']

zmq2_cons = ['ZMQ_MSG_MORE' , 'ZMQ_MSG_SHARED', 'ZMQ_MSG_MASK',
             'ZMQ_UPSTREAM', 'ZMQ_DOWNSTREAM', 'ZMQ_MCAST_LOOP',
             'ZMQ_RECOVERY_IVL_MSEC', 'ZMQ_NOBLOCK', 'ZMQ_HWM',
             'ZMQ_SWAP']

socket_cons = ['ZMQ_PAIR', 'ZMQ_PUB', 'ZMQ_SUB', 'ZMQ_REQ', 'ZMQ_REP',
               'ZMQ_DEALER', 'ZMQ_ROUTER', 'ZMQ_PULL', 'ZMQ_PUSH', 'ZMQ_XPUB',
               'ZMQ_XSUB', 'ZMQ_XREQ', 'ZMQ_XREP']

zmq_base_cons = ['ZMQ_VERSION', 'ZMQ_AFFINITY', 'ZMQ_IDENTITY', 'ZMQ_SUBSCRIBE',
                 'ZMQ_UNSUBSCRIBE', 'ZMQ_RATE', 'ZMQ_RECOVERY_IVL',
                 'ZMQ_SNDBUF', 'ZMQ_RCVBUF', 'ZMQ_RCVMORE', 'ZMQ_FD',
                 'ZMQ_EVENTS', 'ZMQ_TYPE', 'ZMQ_LINGER', 'ZMQ_RECONNECT_IVL',
                 'ZMQ_BACKLOG', 'ZMQ_RECONNECT_IVL_MAX', 'ZMQ_RCVTIMEO',
                 'ZMQ_SNDTIMEO', 'ZMQ_SNDMORE', 'ZMQ_POLLIN', 'ZMQ_POLLOUT',
                 'ZMQ_POLLERR', 'ZMQ_STREAMER', 'ZMQ_FORWARDER', 'ZMQ_QUEUE']

zmq3_cons = ['ZMQ_DONTWAIT', 'ZMQ_MORE', 'ZMQ_MAXMSGSIZE', 'ZMQ_SNDHWM',
             'ZMQ_RCVHWM', 'ZMQ_MULTICAST_HOPS', 'ZMQ_IPV4ONLY',
             'ZMQ_LAST_ENDPOINT', 'ZMQ_ROUTER_BEHAVIOR', 'ZMQ_TCP_KEEPALIVE',
             'ZMQ_TCP_KEEPALIVE_CNT', 'ZMQ_TCP_KEEPALIVE_IDLE',
             'ZMQ_TCP_KEEPALIVE_INTVL', 'ZMQ_TCP_ACCEPT_FILTER',
             'ZMQ_EVENT_CONNECTED', 'ZMQ_EVENT_CONNECT_DELAYED',
             'ZMQ_EVENT_CONNECT_RETRIED', 'ZMQ_EVENT_LISTENING',
             'ZMQ_EVENT_BIND_FAILED', 'ZMQ_EVENT_ACCEPTED',
             'ZMQ_EVENT_ACCEPT_FAILED', 'ZMQ_EVENT_CLOSED',
             'ZMQ_EVENT_CLOSE_FAILED']

core_functions = \
'''
void* zmq_init(int);
int zmq_term(void *context);

void* zmq_socket(void *context, int type);
int zmq_close(void *socket);

int zmq_bind(void *socket, const char *endpoint);
int zmq_connect(void *socket, const char *endpoint);

int zmq_errno(void);
const char * zmq_strerror(int errnum);

void* zmq_stopwatch_start(void);
unsigned long zmq_stopwatch_stop(void *watch);
void zmq_sleep(int seconds_);
'''

core22_functions = \
'''
int zmq_device(int device, const void *frontend, const void *backend);
'''

core32_functions = \
'''
int zmq_unbind(void *socket, const char *endpoint);
int zmq_disconnect(void *socket, const char *endpoint);
void* zmq_ctx_new();
int zmq_ctx_destroy(void *context);
int zmq_proxy(const void *frontend, const void *backend, const void *capture);
'''

message_functions = \
'''
typedef struct {
    void *content;
    unsigned char flags;
    unsigned char vsm_size;
    unsigned char vsm_data [30];
} zmq_msg_t;

typedef ... zmq_free_fn;

int zmq_msg_init(zmq_msg_t *msg);
int zmq_msg_init_size(zmq_msg_t *msg, size_t size);
int zmq_msg_init_data(zmq_msg_t *msg,
                      void *data,
                      size_t size,
                      zmq_free_fn *ffn,
                      void *hint);

size_t zmq_msg_size(zmq_msg_t *msg);
void *zmq_msg_data(zmq_msg_t *msg);
int zmq_msg_close(zmq_msg_t *msg);

int zmq_send(void *socket, zmq_msg_t *msg, int flags);
int zmq_recv(void *socket, zmq_msg_t *msg, int flags);

'''

message32_functions = \
'''
typedef struct {unsigned char _ [32];} zmq_msg_t;
typedef ... zmq_free_fn;

int zmq_msg_init(zmq_msg_t *msg);
int zmq_msg_init_size(zmq_msg_t *msg, size_t size);
int zmq_msg_init_data(zmq_msg_t *msg,
                      void *data,
                      size_t size,
                      zmq_free_fn *ffn,
                      void *hint);

size_t zmq_msg_size(zmq_msg_t *msg);
void *zmq_msg_data(zmq_msg_t *msg);
int zmq_msg_close(zmq_msg_t *msg);

int zmq_msg_send(zmq_msg_t *msg, void *socket, int flags);
int zmq_msg_recv(zmq_msg_t *msg, void *socket, int flags);
'''

sockopt_functions = \
'''
int zmq_getsockopt(void *socket,
                   int option_name,
                   void *option_value,
                   size_t *option_len);

int zmq_setsockopt(void *socket,
                   int option_name,
                   const void *option_value,
                   size_t option_len);
'''

polling_functions = \
'''
typedef struct
{
    void *socket;
    int fd;
    short events;
    short revents;
} zmq_pollitem_t;

int zmq_poll(zmq_pollitem_t *items, int nitems, long timeout);
'''

extra_functions = \
'''
void * memcpy(void *restrict s1, const void *restrict s2, size_t n);
int get_ipc_path_max_len(void);
'''

def zmq_version_info():
    ffi_check = FFI()
    ffi_check.cdef('void zmq_version(int *major, int *minor, int *patch);')
    C_check_version = ffi_check.verify('#include <zmq.h>',
                                            libraries=['c', 'zmq'])
    major = ffi.new('int*')
    minor = ffi.new('int*')
    patch = ffi.new('int*')

    C_check_version.zmq_version(major, minor, patch)

    return (int(major[0]), int(minor[0]), int(patch[0]))

constant_names = errnos + socket_cons + zmq_base_cons + zmq3_cons

def _make_defines(names):
    _names = []
    for name in names:
        define_line = "#define %s ..." % (name)
        _names.append(define_line)

    return "\n".join(_names)

constants = _make_defines(constant_names)

try:
    _version_info = zmq_version_info()
except Exception as e:
    raise ImportError("PyZMQ CFFI backend couldn't find zeromq: %s\n"
    "Please check that you have zeromq headers and libraries." % e)

if _version_info >= (3,2,2):
    functions = ''.join([constants,
                         core_functions,
                         core32_functions,
                         message32_functions,
                         sockopt_functions,
                         polling_functions,
                         extra_functions])
else:
    raise ImportError("PyZMQ CFFI backend requires zeromq >= 3.2.2,"
        " but found %i.%i.%i" % _version_info
    )

ffi.cdef(functions)

C = ffi.verify('''
    #include <string.h>
    #include <zmq.h>
    #include <zmq_utils.h>
    #include <stdio.h>
    #include <sys/un.h>

int get_ipc_path_max_len(void) {
    struct sockaddr_un *dummy;
    return sizeof(dummy->sun_path) - 1;
}

''', libraries=['c', 'zmq'])

nsp = new_sizet_pointer = lambda length: ffi.new('size_t*', length)

new_uint64_pointer = lambda: (ffi.new('uint64_t*'),
                              nsp(ffi.sizeof('uint64_t')))
new_int64_pointer = lambda: (ffi.new('int64_t*'),
                             nsp(ffi.sizeof('int64_t')))
new_int_pointer = lambda: (ffi.new('int*'),
                           nsp(ffi.sizeof('int')))
new_binary_data = lambda length: (ffi.new('char[%d]' % (length)),
                                  nsp(ffi.sizeof('char') * length))

value_uint64_pointer = lambda val : (ffi.new('uint64_t*', val),
                                     ffi.sizeof('uint64_t'))
value_int64_pointer = lambda val: (ffi.new('int64_t*', val),
                                   ffi.sizeof('int64_t'))
value_int_pointer = lambda val: (ffi.new('int*', val),
                                 ffi.sizeof('int'))
value_binary_data = lambda val, length: (ffi.new('char[%d]' % (length), val),
                                         ffi.sizeof('char') * length)

IPC_PATH_MAX_LEN = C.get_ipc_path_max_len()
