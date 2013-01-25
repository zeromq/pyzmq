"""0MQ Constants."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Brian E. Granger & Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .backend import constants

#-----------------------------------------------------------------------------
# Python module level constants
#-----------------------------------------------------------------------------

__all__ = [
    'int_sockopts',
    'int64_sockopts',
    'bytes_sockopts',
    'ctx_opts',
    'ctx_opt_names',
    ]

int_sockopts    = set()
int64_sockopts  = set()
bytes_sockopts  = set()
ctx_opts        = set()
msg_opts        = set()

names = [
    # base
    'VERSION',
    'NOBLOCK',
    'DONTWAIT',

    'POLLIN',
    'POLLOUT',
    'POLLERR',

    'STREAMER',
    'FORWARDER',
    'QUEUE',
    
    'SNDMORE',
    
    # socktypes
    'PAIR',
    'PUB',
    'SUB',
    'REQ',
    'REP',
    'DEALER',
    'ROUTER',
    'PULL',
    'PUSH',
    'XPUB',
    'XSUB',

    # events
    'EVENT_CONNECTED',
    'EVENT_CONNECT_DELAYED',
    'EVENT_CONNECT_RETRIED',
    'EVENT_LISTENING',
    'EVENT_BIND_FAILED',
    'EVENT_ACCEPTED',
    'EVENT_ACCEPT_FAILED',
    'EVENT_CLOSED',
    'EVENT_CLOSE_FAILED',
    'EVENT_DISCONNECTED',
   
    ## ERRNO
    # Often used (these are alse in errno.)
    'EAGAIN',
    'EINVAL',
    'EFAULT',
    'ENOMEM',
    'ENODEV',

    # For Windows compatability
    'ENOTSUP',
    'EPROTONOSUPPORT',
    'ENOBUFS',
    'ENETDOWN',
    'EADDRINUSE',
    'EADDRNOTAVAIL',
    'ECONNREFUSED',
    'EINPROGRESS',
    'ENOTSOCK',

    # new errnos in zmq3
    'EAFNOSUPPORT',
    'EHOSTUNREACH',

    # 0MQ Native
    'EFSM',
    'ENOCOMPATPROTO',
    'ETERM',
    'EMTHREAD',
   
    'EAGAIN',
    'EINVAL',
    'EFAULT',
    'ENOMEM',
    'ENODEV',

    # For Windows compatability
    'ENOTSUP',
    'EPROTONOSUPPORT',
    'ENOBUFS',
    'ENETDOWN',
    'EADDRINUSE',
    'EADDRNOTAVAIL',
    'ECONNREFUSED',
    'EINPROGRESS',
    'ENOTSOCK',

    # new errnos in zmq3
    "EMSGSIZE",
    "EAFNOSUPPORT",
    "ENETUNREACH",
    "ECONNABORTED",
    "ECONNRESET",
    "ENOTCONN",
    "ETIMEDOUT",
    "EHOSTUNREACH",
    "ENETRESET",

    # 0MQ Native
    'EFSM',
    'ENOCOMPATPROTO',
    'ETERM',
    'EMTHREAD',

]

int64_sockopt_names = [
    'AFFINITY',
    'MAXMSGSIZE',

    # sockopts removed in 3.0.0
    'HWM',
    'SWAP',
    'MCAST_LOOP',
    'RECOVERY_IVL_MSEC',
]

bytes_sockopt_names = [
    'IDENTITY',
    'SUBSCRIBE',
    'UNSUBSCRIBE',
    'LAST_ENDPOINT',
    'TCP_ACCEPT_FILTER',
]

int_sockopt_names = [
    # sockopts
    'RECONNECT_IVL_MAX',

    # sockopts new in 2.2.0
    'SNDTIMEO',
    'RCVTIMEO',

    # new in 3.x
    'SNDHWM',
    'RCVHWM',
    'MULTICAST_HOPS',
    'IPV4ONLY',

    'ROUTER_BEHAVIOR',
    'TCP_KEEPALIVE',
    'TCP_KEEPALIVE_CNT',
    'TCP_KEEPALIVE_IDLE',
    'TCP_KEEPALIVE_INTVL',
    'DELAY_ATTACH_ON_CONNECT',
    'XPUB_VERBOSE',
    'ROUTER_RAW',

    'FD',
    'EVENTS',
    'TYPE',
    'LINGER',
    'RECONNECT_IVL',
    'BACKLOG',
]

ctx_opt_names = [
    'IO_THREADS',
    'MAX_SOCKETS',
]

msg_opt_names = [
    'MORE',
]

switched_names = [
    'RATE',
    'RECOVERY_IVL',
    'SNDBUF',
    'RCVBUF',
    'RCVMORE',
]

if constants.VERSION < 30000:
    int64_sockopt_names.extend(switched_names)
else:
    int_sockopt_names.extend(switched_names)

def _add_constant(name, container=None):
    c = getattr(constants, name, -1)
    if c == -1:
        return
    globals()[name] = c
    __all__.append(name)
    if container is not None:
        container.add(c)
    return c
    
for name in names:
    _add_constant(name)

for name in int_sockopt_names:
    _add_constant(name, int_sockopts)

for name in int64_sockopt_names:
    _add_constant(name, int64_sockopts)

for name in bytes_sockopt_names:
    _add_constant(name, bytes_sockopts)

for name in ctx_opt_names:
    _add_constant(name, ctx_opts)

for name in msg_opt_names:
    _add_constant(name, msg_opts)


