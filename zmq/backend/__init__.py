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
import platform
import sys

from zmq.utils.sixcerpt import reraise

from .select import public_api, select_backend

if 'PYZMQ_BACKEND' in os.environ:
    backend = os.environ['PYZMQ_BACKEND']
    if backend in ('cython', 'cffi'):
        backend = 'zmq.backend.%s' % backend
    _ns = select_backend(backend)
else:
    # default to cython, fallback to cffi
    # (reverse on PyPy)
    if platform.python_implementation() == 'PyPy':
        first, second = ('zmq.backend.cffi', 'zmq.backend.cython')
    else:
        first, second = ('zmq.backend.cython', 'zmq.backend.cffi')

    try:
        _ns = select_backend(first)
    except Exception:
        exc_info = sys.exc_info()
        try:
            _ns = select_backend(second)
        except ImportError:
            # raise the *first* error, not the fallback
            reraise(*exc_info)

globals().update(_ns)

__all__ = public_api
