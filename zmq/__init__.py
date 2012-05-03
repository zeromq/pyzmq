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
import glob

here = os.path.dirname(__file__)
bundled = glob.glob(os.path.join(here, 'libzmq.*'))
if bundled:
    import ctypes
    _libzmq = ctypes.CDLL(bundled[0], mode=ctypes.RTLD_GLOBAL)
    print _libzmq
    del ctypes

del os, glob, here, bundled

from zmq.utils import initthreads # initialize threads
initthreads.init_threads()

from zmq import core, devices
from zmq.core import *

def get_includes():
    """Return a list of directories to include for linking against pyzmq with cython."""
    from os.path import join, dirname, abspath, pardir
    base = dirname(__file__)
    parent = abspath(join(base, pardir))
    return [ parent ] + [ join(parent, base, subdir) for subdir in ('utils',) ]


__all__ = ['get_includes'] + core.__all__

