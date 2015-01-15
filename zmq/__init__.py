"""Python bindings for 0MQ."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import os
import sys
import glob

# load bundled libzmq, if there is one:

here = os.path.dirname(__file__)

bundled = []
bundled_sodium = []
for ext in ('pyd', 'so', 'dll', 'dylib'):
    bundled_sodium.extend(glob.glob(os.path.join(here, 'libsodium*.%s*' % ext)))
    bundled.extend(glob.glob(os.path.join(here, 'libzmq*.%s*' % ext)))

if bundled:
    import ctypes
    if bundled_sodium:
        if bundled[0].endswith('.pyd'):
            # a Windows Extension
            _libsodium = ctypes.cdll.LoadLibrary(bundled_sodium[0])
        else:
            _libsodium = ctypes.CDLL(bundled_sodium[0], mode=ctypes.RTLD_GLOBAL)
    if bundled[0].endswith('.pyd'):
        # a Windows Extension
        _libzmq = ctypes.cdll.LoadLibrary(bundled[0])
    else:
        _libzmq = ctypes.CDLL(bundled[0], mode=ctypes.RTLD_GLOBAL)
    del ctypes
else:
    import zipimport
    try:
        if isinstance(__loader__, zipimport.zipimporter):
            # a zipped pyzmq egg
            from zmq import libzmq as _libzmq
    except (NameError, ImportError):
        pass
    finally:
        del zipimport

del os, sys, glob, here, bundled, bundled_sodium, ext

# zmq top-level imports

from zmq import backend
from zmq.backend import *
from zmq import sugar
from zmq.sugar import *
from zmq import devices

def get_includes():
    """Return a list of directories to include for linking against pyzmq with cython."""
    from os.path import join, dirname, abspath, pardir
    base = dirname(__file__)
    parent = abspath(join(base, pardir))
    return [ parent ] + [ join(parent, base, subdir) for subdir in ('utils',) ]


__all__ = ['get_includes'] + sugar.__all__ + backend.__all__

