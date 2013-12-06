# coding: utf-8
"""zmq version function"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2014 Pawel Jasinski
#  Derived from pyzmq-ctypes Copyright (C) 2011 Daniel Holth
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from ._iron_ctypes import libzmq
from ctypes import c_int, byref
_major = c_int()
_minor = c_int()
_patch = c_int()

libzmq.zmq_version(byref(_major), byref(_minor), byref(_patch))

__zmq_version__ = tuple((x.value for x in (_major, _minor, _patch)))

def zmq_version_info():
    return __zmq_version__

if __zmq_version__ < (4,0,0):
    raise ImportError("PyZMQ IronPython backend requires zeromq >= 4.0.0,"
        " but found %i.%i.%i" % _version_info
    )

__all__ = ['zmq_version_info']
