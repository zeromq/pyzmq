"""0MQ Constant names"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

#-----------------------------------------------------------------------------
# Python module level constants
#-----------------------------------------------------------------------------

# dictionaries of constants new or removed in particular versions

new_in = {
    (2,2,0) : [
        'RCVTIMEO',
        'SNDTIMEO',
    ],
    (3,2,2) : [
        # errnos
        'EMSGSIZE',
        'EAFNOSUPPORT',
        'ENETUNREACH',
        'ECONNABORTED',
        'ECONNRESET',
        'ENOTCONN',
        'ETIMEDOUT',
        'EHOSTUNREACH',
        'ENETRESET',
        
        'IO_THREADS',
        'MAX_SOCKETS',
        'IO_THREADS_DFLT',
        'MAX_SOCKETS_DFLT',
        
        'ROUTER_BEHAVIOR',
        'ROUTER_MANDATORY',
        'FAIL_UNROUTABLE',
        'TCP_KEEPALIVE',
        'TCP_KEEPALIVE_CNT',
        'TCP_KEEPALIVE_IDLE',
        'TCP_KEEPALIVE_INTVL',
        'DELAY_ATTACH_ON_CONNECT',
        'XPUB_VERBOSE',
        
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
        'EVENT_ALL',
    ],
    (4,0,0) : [
        # socket types
        'STREAM',
        
        # socket opts
        'IMMEDIATE',
        'ROUTER_RAW',
        'IPV6',
        'MECHANISM',
        'PLAIN_SERVER',
        'PLAIN_USERNAME',
        'PLAIN_PASSWORD',
        'CURVE_SERVER',
        'CURVE_PUBLICKEY',
        'CURVE_SECRETKEY',
        'CURVE_SERVERKEY',
        'PROBE_ROUTER',
        'REQ_RELAXED',
        'REQ_CORRELATE',
        'CONFLATE',
        'ZAP_DOMAIN',
        
        # security
        'NULL',
        'PLAIN',
        'CURVE',
        
        # events
        'EVENT_MONITOR_STOPPED',
    ],
    (4,1,0) : [
        # socket opts
        'ROUTER_HANDOVER',
        'TOS',
        'IPC_FILTER_PID',
        'IPC_FILTER_UID',
        'IPC_FILTER_GID',
        'CONNECT_RID',
    ],
}


removed_in = {
    (3,2,2) : [
        'UPSTREAM',
        'DOWNSTREAM',
        
        'HWM',
        'SWAP',
        'MCAST_LOOP',
        'RECOVERY_IVL_MSEC',
    ]
}

# collections of zmq constant names based on their role
# base names have no specific use
# opt names are validated in get/set methods of various objects

base_names = [
    # base
    'VERSION',
    'VERSION_MAJOR',
    'VERSION_MINOR',
    'VERSION_PATCH',
    'NOBLOCK',
    'DONTWAIT',

    'POLLIN',
    'POLLOUT',
    'POLLERR',
    
    'SNDMORE',

    'STREAMER',
    'FORWARDER',
    'QUEUE',

    'IO_THREADS_DFLT',
    'MAX_SOCKETS_DFLT',

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
    'UPSTREAM',
    'DOWNSTREAM',
    'STREAM',

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
    'EVENT_ALL',
    'EVENT_MONITOR_STOPPED',

    # security
    'NULL',
    'PLAIN',
    'CURVE',

    ## ERRNO
    # Often used (these are alse in errno.)
    'EAGAIN',
    'EINVAL',
    'EFAULT',
    'ENOMEM',
    'ENODEV',
    'EMSGSIZE',
    'EAFNOSUPPORT',
    'ENETUNREACH',
    'ECONNABORTED',
    'ECONNRESET',
    'ENOTCONN',
    'ETIMEDOUT',
    'EHOSTUNREACH',
    'ENETRESET',

    # For Windows compatability
    'HAUSNUMERO',
    'ENOTSUP',
    'EPROTONOSUPPORT',
    'ENOBUFS',
    'ENETDOWN',
    'EADDRINUSE',
    'EADDRNOTAVAIL',
    'ECONNREFUSED',
    'EINPROGRESS',
    'ENOTSOCK',

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

    'PLAIN_USERNAME',
    'PLAIN_PASSWORD',

    'CURVE_PUBLICKEY',
    'CURVE_SECRETKEY',
    'CURVE_SERVERKEY',
    'ZAP_DOMAIN',
    'CONNECT_RID',
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

    'FD',
    'EVENTS',
    'TYPE',
    'LINGER',
    'RECONNECT_IVL',
    'BACKLOG',
    
    'ROUTER_MANDATORY',
    'FAIL_UNROUTABLE',

    'ROUTER_RAW',
    'IMMEDIATE',
    'IPV6',
    'MECHANISM',
    'PLAIN_SERVER',
    'CURVE_SERVER',
    'PROBE_ROUTER',
    'REQ_RELAXED',
    'REQ_CORRELATE',
    'CONFLATE',
    'ROUTER_HANDOVER',
    'TOS',
    'IPC_FILTER_PID',
    'IPC_FILTER_UID',
    'IPC_FILTER_GID',
]

switched_sockopt_names = [
    'RATE',
    'RECOVERY_IVL',
    'SNDBUF',
    'RCVBUF',
    'RCVMORE',
]

ctx_opt_names = [
    'IO_THREADS',
    'MAX_SOCKETS',
]

msg_opt_names = [
    'MORE',
]

all_names = (
    base_names + ctx_opt_names + msg_opt_names +
    bytes_sockopt_names + int_sockopt_names + int64_sockopt_names + switched_sockopt_names
)

def no_prefix(name):
    """does the given constant have a ZMQ_ prefix?"""
    return name.startswith('E') and not name.startswith('EVENT')

