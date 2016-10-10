"""Python bindings for 0MQ."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

# load bundled libzmq, if there is one:
def _load_libzmq():
    """load bundled libzmq if there is one"""
    import sys, ctypes, platform
    dlopen = hasattr(sys, 'getdlopenflags') # unix-only
    if dlopen:
        dlflags = sys.getdlopenflags()
        sys.setdlopenflags(ctypes.RTLD_GLOBAL | dlflags)
    try:
        from . import libzmq
    except ImportError:
        pass
    else:
        # store libzmq as zmq._libzmq for backward-compat
        globals()['_libzmq'] = libzmq
        if platform.python_implementation().lower() == 'pypy':
            # pypy needs explicit CDLL load for some reason,
            # otherwise symbols won't be globally available
            ctypes.CDLL(libzmq.__file__, ctypes.RTLD_GLOBAL)
    finally:
        if dlopen:
            sys.setdlopenflags(dlflags)

_load_libzmq()


# zmq top-level imports

from zmq import backend
from zmq.backend import *
from zmq import sugar
from zmq.sugar import *

def get_includes():
    """Return a list of directories to include for linking against pyzmq with cython."""
    from os.path import join, dirname, abspath, pardir, exists
    base = dirname(__file__)
    parent = abspath(join(base, pardir))
    includes = [ parent ] + [ join(parent, base, subdir) for subdir in ('utils',) ]
    if exists(join(parent, base, 'include')):
        includes.append(join(parent, base, 'include'))
    return includes
    
def get_library_dirs():
    """Return a list of directories used to link against pyzmq's bundled libzmq."""
    from os.path import join, dirname, abspath, pardir
    base = dirname(__file__)
    parent = abspath(join(base, pardir))
    return [ join(parent, base) ]


__all__ = ['get_includes'] + sugar.__all__ + backend.__all__
