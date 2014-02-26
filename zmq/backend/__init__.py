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

import os
from .select import public_api, select_backend

if 'PYZMQ_BACKEND' in os.environ:
    backend = os.environ['PYZMQ_BACKEND']
    if backend in ('cython', 'cffi'):
        backend = 'zmq.backend.%s' % backend
    _ns = select_backend(backend)
else:
    # default to cython, fallback to cffi
    try:
        _ns = select_backend('zmq.backend.cython')
    except ImportError:
        _ns = select_backend('zmq.backend.cffi')

globals().update(_ns)

__all__ = public_api
