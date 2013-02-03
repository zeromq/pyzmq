# coding: utf-8
"""zmq constants"""

from ._cffi import zmq_version_info

# Modified by Felipe Cruz
# Copyright © 2011 Daniel Holth
#
# Derived from original pyzmq © 2010 Brian Granger
#
# This file is part of pyzmq-ctypes
#
# pyzmq-ctypes is free software; you can redistribute it and/or modify it
# under the terms of the Lesser GNU General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# pyzmq-ctypes is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the Lesser GNU General Public
# License for more details.
#
# You should have received a copy of the Lesser GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

from ctypes import *
from ctypes.util import find_library
from ctypes_configure import configure

class CConfigure(object):
    _compilation_info_ = configure.ExternalCompilationInfo(includes=['zmq.h'],
                                                           libraries=['zmq'])

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

names = None
pynames = []

if zmq_version_info()[0] == 2:
    names = errnos + socket_cons + zmq_base_cons + zmq2_cons
else:
    names = errnos + socket_cons + zmq_base_cons + zmq3_cons

for cname in names:
    pyname = cname.split('_', 1)[-1]
    pynames.append(pyname)
    setattr(CConfigure, pyname, configure.ConstantInteger(cname))

_constants = configure.configure(CConfigure)
globals().update(_constants)

if zmq_version_info()[0] == 2:
    DONTWAIT = NOBLOCK
else:
    NOBLOCK = DONTWAIT

__all__ = pynames
