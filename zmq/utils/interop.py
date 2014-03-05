"""Utils for interoperability with other libraries.

Just CFFI pointer casting for now.
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2014 Brian E. Granger & Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------


try:
    long
except NameError:
    long = int # Python 3


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
