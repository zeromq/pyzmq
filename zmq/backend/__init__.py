"""Import basic exposure of libzmq C API as a backend"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .select import public_api, select_backend

import sys
if sys.platform != 'cli':
    try:
        _ns = select_backend('zmq.backend.cython')
    except ImportError:
        _ns = select_backend('zmq.backend.cffi')
else:
    _ns = select_backend('zmq.backend.ctypes')
del sys
globals().update(_ns)

__all__ = public_api
