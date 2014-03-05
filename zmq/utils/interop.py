"""Interoperability with other libraries.

Just pyczmq, for now.
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2014 Brian E. Granger & Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import zmq

try:
    long
except NameError:
    long = int # Python 3

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def socket_from_pyczmq(void_p):
    """Create a zmq.Socket from pyczmq
    
    void_p is a CFFI `void *`
    """
    return zmq.Socket.from_address(void_p)


def context_from_pyczmq(zctx_p):
    """Create a zmq.Context from pyczmq
    
    zctx_p is a CFFI `zctx_t *`
    """
    from pyczmq import zctx
    ptr = zctx.underlying(ctx)
    return zmq.Context.from_address(ptr)


def cast_int_addr(n):
    """Cast an address to a Python int
    
    This could be a Python integer or a CFFI pointer
    """
    if isinstance(n, (int, long)):
        return n
    try:
        import cffi
    except ImportError:
        pass
    else:
        # from pyzmq, this is an FFI void *
        ffi = cffi.FFI()
        if isinstance(n, ffi.CData):
            return int(ffi.cast("size_t", n))
    
    raise ValueError("Cannot cast %r to int" % n)

