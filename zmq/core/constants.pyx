"""0MQ Constants."""

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

from libzmq cimport *

#-----------------------------------------------------------------------------
# Python module level constants
#-----------------------------------------------------------------------------

_optionals = []

if ZMQ_VERSION < 30000:
    # backport DONTWAIT as alias to NOBLOCK
    NOBLOCK = ZMQ_NOBLOCK
    DONTWAIT = ZMQ_NOBLOCK
else:
    # keep NOBLOCK as alias for new DONTWAIT
    NOBLOCK = ZMQ_DONTWAIT
    DONTWAIT = ZMQ_DONTWAIT

VERSION = ZMQ_VERSION

# socket types
PAIR = ZMQ_PAIR
PUB = ZMQ_PUB
SUB = ZMQ_SUB
REQ = ZMQ_REQ
REP = ZMQ_REP
DEALER = ZMQ_DEALER
ROUTER = ZMQ_ROUTER
PULL = ZMQ_PULL
PUSH = ZMQ_PUSH
XPUB = ZMQ_XPUB
XSUB = ZMQ_XSUB

# keep deprecated aliases
XREQ = DEALER
XREP = ROUTER
UPSTREAM = PULL
DOWNSTREAM = PUSH


# socket options
AFFINITY = ZMQ_AFFINITY
IDENTITY = ZMQ_IDENTITY
SUBSCRIBE = ZMQ_SUBSCRIBE
UNSUBSCRIBE = ZMQ_UNSUBSCRIBE
RATE = ZMQ_RATE
RECOVERY_IVL = ZMQ_RECOVERY_IVL
RECONNECT_IVL_MAX = ZMQ_RECONNECT_IVL_MAX
SNDBUF = ZMQ_SNDBUF
RCVBUF = ZMQ_RCVBUF
RCVMORE = ZMQ_RCVMORE
SNDMORE = ZMQ_SNDMORE
POLLIN = ZMQ_POLLIN
POLLOUT = ZMQ_POLLOUT
POLLERR = ZMQ_POLLERR

STREAMER = ZMQ_STREAMER
FORWARDER = ZMQ_FORWARDER
QUEUE = ZMQ_QUEUE

# sockopts new in 2.2.0
SNDTIMEO = ZMQ_SNDTIMEO
RCVTIMEO = ZMQ_RCVTIMEO

# sockopts removed in 3.0.0
HWM = ZMQ_HWM
SWAP = ZMQ_SWAP
MCAST_LOOP = ZMQ_MCAST_LOOP
RECOVERY_IVL_MSEC = ZMQ_RECOVERY_IVL_MSEC

# new in 3.x
IO_THREADS = ZMQ_IO_THREADS
MAX_SOCKETS = ZMQ_MAX_SOCKETS

MORE = ZMQ_MORE
    
MAXMSGSIZE = ZMQ_MAXMSGSIZE
SNDHWM = ZMQ_SNDHWM
RCVHWM = ZMQ_RCVHWM
MULTICAST_HOPS = ZMQ_MULTICAST_HOPS
IPV4ONLY = ZMQ_IPV4ONLY
LAST_ENDPOINT = ZMQ_LAST_ENDPOINT

ROUTER_MANDATORY = ZMQ_ROUTER_MANDATORY
# aliases
ROUTER_BEHAVIOR = ROUTER_MANDATORY
FAIL_UNROUTABLE = ROUTER_MANDATORY

TCP_KEEPALIVE = ZMQ_TCP_KEEPALIVE
TCP_KEEPALIVE_CNT = ZMQ_TCP_KEEPALIVE_CNT
TCP_KEEPALIVE_IDLE = ZMQ_TCP_KEEPALIVE_IDLE
TCP_KEEPALIVE_INTVL = ZMQ_TCP_KEEPALIVE_INTVL
TCP_ACCEPT_FILTER = ZMQ_TCP_ACCEPT_FILTER
DELAY_ATTACH_ON_CONNECT = ZMQ_DELAY_ATTACH_ON_CONNECT
XPUB_VERBOSE = ZMQ_XPUB_VERBOSE
ROUTER_RAW = ZMQ_ROUTER_RAW

EVENT_CONNECTED = ZMQ_EVENT_CONNECTED
EVENT_CONNECT_DELAYED = ZMQ_EVENT_CONNECT_DELAYED
EVENT_CONNECT_RETRIED = ZMQ_EVENT_CONNECT_RETRIED
EVENT_LISTENING = ZMQ_EVENT_LISTENING
EVENT_BIND_FAILED = ZMQ_EVENT_BIND_FAILED
EVENT_ACCEPTED = ZMQ_EVENT_ACCEPTED
EVENT_ACCEPT_FAILED = ZMQ_EVENT_ACCEPT_FAILED
EVENT_CLOSED = ZMQ_EVENT_CLOSED
EVENT_CLOSE_FAILED = ZMQ_EVENT_CLOSE_FAILED
EVENT_DISCONNECTED = ZMQ_EVENT_DISCONNECTED

FD = ZMQ_FD
EVENTS = ZMQ_EVENTS
TYPE = ZMQ_TYPE
LINGER = ZMQ_LINGER
RECONNECT_IVL = ZMQ_RECONNECT_IVL
BACKLOG = ZMQ_BACKLOG

# As new constants are added in future versions, add a new block here
# like the two above, checking agains the relevant value for ZMQ_VERSION.
# The constants will need to be added to libzmq.pxd and utils/zmq_compat.h
# as well.

#-----------------------------------------------------------------------------
# Error handling
#-----------------------------------------------------------------------------

# Often used standard errnos
from errno import (
    EAGAIN,
    EINVAL,
    EFAULT,
    ENOMEM,
    ENODEV
)

# For Windows compatability
ENOTSUP = ZMQ_ENOTSUP
EPROTONOSUPPORT = ZMQ_EPROTONOSUPPORT
ENOBUFS = ZMQ_ENOBUFS
ENETDOWN = ZMQ_ENETDOWN
EADDRINUSE = ZMQ_EADDRINUSE
EADDRNOTAVAIL = ZMQ_EADDRNOTAVAIL
ECONNREFUSED = ZMQ_ECONNREFUSED
EINPROGRESS = ZMQ_EINPROGRESS
ENOTSOCK = ZMQ_ENOTSOCK

# new errnos in zmq3
EMSGSIZE = ZMQ_EMSGSIZE
EAFNOSUPPORT = ZMQ_EAFNOSUPPORT
ENETUNREACH = ZMQ_ENETUNREACH
ECONNABORTED = ZMQ_ECONNABORTED
ECONNRESET = ZMQ_ECONNRESET
ENOTCONN = ZMQ_ENOTCONN
ETIMEDOUT = ZMQ_ETIMEDOUT
EHOSTUNREACH = ZMQ_EHOSTUNREACH
ENETRESET = ZMQ_ENETRESET

# 0MQ Native
EFSM = ZMQ_EFSM
ENOCOMPATPROTO = ZMQ_ENOCOMPATPROTO
ETERM = ZMQ_ETERM
EMTHREAD = ZMQ_EMTHREAD

#-----------------------------------------------------------------------------
# Symbols to export
#-----------------------------------------------------------------------------
_names = list(locals().keys())
__all__ = [ key for key in _names if not key.startswith('_') ]
