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

pypy_install = 'PyPy' in sys.version

if pypy_install:
    import types
    from zmq.cffi_core._cffi import zmq_version_info, zmq_version, \
                                    IPC_PATH_MAX_LEN
    from zmq.cffi_core import _poll, constants, context, message, version, \
                              eventloop
    from zmq.cffi_core.constants import *
    from zmq.cffi_core.context import *
    from zmq.cffi_core.version import *
    from zmq.cffi_core._poll import *
    from zmq.cffi_core.message import *
    from zmq.cffi_core.eventloop import *
    from zmq.cffi_core import *
    import zmq.cffi_core as core

    #fake modules just to pass imports
    devices = types.ModuleType('device')

    sys.modules['zmq.core'] = core
    sys.modules['zmq.core._poll'] = _poll
    sys.modules['zmq.core.constants'] = constants
    sys.modules['zmq.core.context'] = context
    sys.modules['zmq.core.message'] = message
    sys.modules['zmq.core.version'] = version
    sys.modules['zmq.devices'] = devices
    sys.modules['zmq.eventloop'] = eventloop

else:
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
