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

# If we are running in a debug interpreter, load libzmq_d.pyd instead of libzmq.pyd
# hasattr(sys, 'gettotalrefcount') is used to detect whether we are running in a debug interpreter
# Taken from http://stackoverflow.com/questions/646518/python-how-to-detect-debug-interpreter
if os.name == 'nt':
    def is_debug_filename(name):
        # Note this fails for filenames like foo.bar_d.so.x.y.z,
        # but such names should not appear on Windows.
        root, ext = os.path.splitext(name)
        return root.endswith('_d')

    if hasattr(sys, 'gettotalrefcount'):
        bundled_sodium = [x for x in bundled_sodium if is_debug_filename(x)]
        bundled = [x for x in bundled if is_debug_filename(x)]
    else:
        bundled_sodium = [x for x in bundled_sodium if not is_debug_filename(x)]
        bundled = [x for x in bundled if not is_debug_filename(x)]

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

