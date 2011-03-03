"""0MQ Constants."""

#
#    Copyright (c) 2010 Brian E. Granger
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

from czmq cimport *

#-----------------------------------------------------------------------------
# Python module level constants
#-----------------------------------------------------------------------------

_optionals = []

NOBLOCK = ZMQ_NOBLOCK
# socket types
PAIR = ZMQ_PAIR
PUB = ZMQ_PUB
SUB = ZMQ_SUB
REQ = ZMQ_REQ
REP = ZMQ_REP
XREQ = ZMQ_XREQ
XREP = ZMQ_XREP
PULL = ZMQ_PULL
PUSH = ZMQ_PUSH
UPSTREAM = ZMQ_UPSTREAM
DOWNSTREAM = ZMQ_DOWNSTREAM
# new in 2.1.1
if ZMQ_VERSION >= 20101:
    XPUB = ZMQ_XPUB
    XSUB = ZMQ_XSUB
    _optionals.extend(['XPUB','XSUB'])

# socket options
HWM = ZMQ_HWM
SWAP = ZMQ_SWAP
AFFINITY = ZMQ_AFFINITY
IDENTITY = ZMQ_IDENTITY
SUBSCRIBE = ZMQ_SUBSCRIBE
UNSUBSCRIBE = ZMQ_UNSUBSCRIBE
RATE = ZMQ_RATE
RECOVERY_IVL = ZMQ_RECOVERY_IVL
MCAST_LOOP = ZMQ_MCAST_LOOP
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

# collections of sockopts, based on type:
bytes_sockopts = [SUBSCRIBE, UNSUBSCRIBE, IDENTITY]
int64_sockopts = [HWM, SWAP, AFFINITY, RATE, RECOVERY_IVL,
                MCAST_LOOP, SNDBUF, RCVBUF, RCVMORE]
int_sockopts = []

# new sockopts in 2.1.0:
if ZMQ_VERSION >= 20100:
    FD = ZMQ_FD
    EVENTS = ZMQ_EVENTS
    TYPE = ZMQ_TYPE
    LINGER = ZMQ_LINGER
    RECONNECT_IVL = ZMQ_RECONNECT_IVL
    BACKLOG = ZMQ_BACKLOG
    int_sockopts.extend([FD, EVENTS, TYPE, LINGER, RECONNECT_IVL, BACKLOG])
    _optionals.extend('FD EVENTS TYPE LINGER RECONNECT_IVL BACKLOG'.split())

# new in 2.1.1:
if ZMQ_VERSION >= 20101:
    RECOVERY_IVL_MSEC = ZMQ_RECOVERY_IVL_MSEC
    RECONNECT_IVL_MAX = ZMQ_RECONNECT_IVL_MAX
    int64_sockopts.extend([RECOVERY_IVL_MSEC, RECONNECT_IVL_MAX])
    _optionals.extend('RECOVERY_IVL_MSEC RECONNECT_IVL_MAX'.split())

# As new constants are added in future versions, add a new block here
# like the two above, checking agains the relevant value for ZMQ_VERSION.
# The constants will need to be added to czmq.pxd and utils/zmq_compat.h
# as well.

#-----------------------------------------------------------------------------
# Error handling
#-----------------------------------------------------------------------------

# Often used (these are alse in errno.)
EAGAIN = ZMQ_EAGAIN
EINVAL = ZMQ_EINVAL
EFAULT = ZMQ_EFAULT
ENOMEM = ZMQ_ENOMEM
ENODEV = ZMQ_ENODEV

# For Windows compatability
ENOTSUP = ZMQ_ENOTSUP
EPROTONOSUPPORT = ZMQ_EPROTONOSUPPORT
ENOBUFS = ZMQ_ENOBUFS
ENETDOWN = ZMQ_ENETDOWN
EADDRINUSE = ZMQ_EADDRINUSE
EADDRNOTAVAIL = ZMQ_EADDRNOTAVAIL
ECONNREFUSED = ZMQ_ECONNREFUSED
EINPROGRESS = ZMQ_EINPROGRESS

# 0MQ Native
EMTHREAD = ZMQ_EMTHREAD
EFSM = ZMQ_EFSM
ENOCOMPATPROTO = ZMQ_ENOCOMPATPROTO
ETERM = ZMQ_ETERM

#-----------------------------------------------------------------------------
# Symbols to export
#-----------------------------------------------------------------------------

__all__ = [
    'NOBLOCK',
    'PAIR',
    'PUB',
    'SUB',
    'REQ',
    'REP',
    'XREQ',
    'XREP',
    'PULL',
    'PUSH',
    'UPSTREAM',
    'DOWNSTREAM',
    'HWM',
    'SWAP',
    'AFFINITY',
    'IDENTITY',
    'SUBSCRIBE',
    'UNSUBSCRIBE',
    'RATE',
    'RECOVERY_IVL',
    'MCAST_LOOP',
    'SNDBUF',
    'RCVBUF',
    'SNDMORE',
    'RCVMORE',
    'POLLIN',
    'POLLOUT',
    'POLLERR',
    'STREAMER',
    'FORWARDER',
    'QUEUE',
    # ERRORNO codes
    'EAGAIN',
    'EINVAL',
    'ENOTSUP',
    'EPROTONOSUPPORT',
    'ENOBUFS',
    'ENETDOWN',
    'EADDRINUSE',
    'EADDRNOTAVAIL',
    'ECONNREFUSED',
    'EINPROGRESS',
    'EMTHREAD',
    'EFSM',
    'ENOCOMPATPROTO',
    'ETERM',
    'EFAULT',
    'ENOMEM',
    'ENODEV',
    # collections
    'bytes_sockopts',
    'int_sockopts',
    'int64_sockopts'
]
__all__.extend(_optionals)
del _optionals
