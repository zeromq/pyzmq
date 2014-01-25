# coding: utf-8
"""zmq error functions"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz, Pawel Jasinski
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from ._ctypes import libzmq

def strerror(errno):
    return libzmq.zmq_strerror(errno)

zmq_errno = libzmq.zmq_errno

__all__ = ['strerror', 'zmq_errno']
