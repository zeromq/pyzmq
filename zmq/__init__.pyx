"""Python bindings for 0MQ."""

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

cdef extern from "Python.h":
    cdef void PyEval_InitThreads()

# It seems that in only *some* version of Python/Cython we need to call this
# by hand to get threads initialized. Not clear why this is the case though.
# If we don't have this, pyzmq will segfault.
PyEval_InitThreads()

from zmq cimport zmq_device, _zmq_version
from zmq.core.socket cimport Socket as cSocket

from zmq import core
from zmq.core.context import Context
from zmq.core.socket import Socket
from zmq.core.message import Message, MessageTracker
from zmq.core.error import *
from zmq.core.constants import *
from zmq.core.poll import Poller, select
from zmq.core.stopwatch import Stopwatch


#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

__version__ = '2.0.9dev'

def zmq_version():
    """Return the version of ZeroMQ itself."""
    cdef int major, minor, patch
    _zmq_version(&major, &minor, &patch)
    return '%i.%i.%i' % (major, minor, patch)

#-----------------------------------------------------------------------------
# Basic device API
#-----------------------------------------------------------------------------
# 
def device(int device_type, cSocket isocket, cSocket osocket):
    """Start a zeromq device.

    Parameters
    ----------
    device_type : (QUEUE, FORWARDER, STREAMER)
        The type of device to start.
    isocket : Socket
        The Socket instance for the incoming traffic.
    osocket : Socket
        The Socket instance for the outbound traffic.
    """
    cdef int result = 0
    with nogil:
        result = zmq_device(device_type, isocket.handle, osocket.handle)
    return result


def get_includes():
    from os.path import join, dirname
    base = dirname(__file__)
    return [ join(base, subdir) for subdir in ('core', 'devices', 'utils')]


# __all__ = ['get_includes']

