"""Python bindings for 0MQ."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2012 Brian Granger, Min Ragan-Kelley
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
import sys
import glob

# load bundled libzmq, if there is one:

here = os.path.dirname(__file__)

bundled = []
for ext in ('pyd', 'so', 'dll', 'dylib'):
    bundled.extend(glob.glob(os.path.join(here, 'libzmq*.%s*' % ext)))

if bundled:
    import ctypes
    if bundled[0].endswith('.pyd'):
        # a Windows Extension
        _libzmq = ctypes.cdll.LoadLibrary(bundled[0])
    else:
        _libzmq = ctypes.CDLL(bundled[0], mode=ctypes.RTLD_GLOBAL)
    del ctypes

del os, sys, glob, here, bundled, ext

# init Python threads

try:
    from zmq.utils import initthreads # initialize threads
except ImportError as e:
    raise ImportError("%s\nAre you trying to `import zmq` from the pyzmq source dir?" % e)

initthreads.init_threads()

# zmq top-level imports

from zmq import core, devices
from zmq.core import *

def get_includes():
    """Return a list of directories to include for linking against pyzmq with cython."""
    from os.path import join, dirname, abspath, pardir
    base = dirname(__file__)
    parent = abspath(join(base, pardir))
    return [ parent ] + [ join(parent, base, subdir) for subdir in ('utils',) ]


__all__ = ['get_includes'] + core.__all__

