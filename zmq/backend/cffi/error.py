"""zmq error functions"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from ._cffi import C, ffi

def strerror(errno):
    return ffi.string(C.zmq_strerror(errno))

zmq_errno = C.zmq_errno

__all__ = ['strerror', 'zmq_errno']
