# coding: utf-8
"""zmq constants"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz, Pawel Jasinski
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from zmq.utils.constant_names import all_names

# ZMQ.py is generated from zmq.h during setup h2py.py
import ZMQ
g = globals()
for cname, cvalue in ZMQ.__dict__.iteritems():
    if cname.startswith("__"):
        continue
    if cname.startswith("ZMQ_"):
        cname = cname[4:]
    g[cname] = cvalue

# ERRNO.py was generated out of system errno.h using h2py.py
#
# Standard python errno module (Ironpython 2.7.4) cannot be used, because
# ironpython uses WSA values which do not match posix values. For example:
# errno.EADDRINUSE in ironpython is 10048 which is WSAEADDRINUSE
# errno.EADDRINUSE returned by libzmq is 100

from .ERRNO import *
VERSION = "%d%02d%02d" % (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)


# extract the actual library version
from ._version import zmq_version_info
LIB_VERSION_MAJOR, LIB_VERSION_MINOR, LIB_VERSION_PATCH = zmq_version_info()
LIB_VERSION = "%d%02d%02d" % zmq_version_info()
# cross check loaded library version with one used during setup
if LIB_VERSION != VERSION:
    if LIB_VERSION_MAJOR != VERSION_MAJOR:
        raise Exception("""
Version of libzmq used during install is different than loaded one.
Please, rerun setup with --bin-only-zmq pointing to the actual libzmq distribution.
(setup version: %s, loaded version: %s)""" % (VERSION, LIB_VERSION))
    import warnings
    warnings.warn("""
Version of libzmq used during install is different than loaded one.
Please, rerun setup with --bin-only-zmq pointing to the actual libzmq distribution.
Some tests are known to fail. (setup version: %s, loaded version: %s)""" % (VERSION, LIB_VERSION))
    del warnings

VERSION = LIB_VERSION
VERSION_MAJOR = LIB_VERSION_MAJOR
VERSION_MINOR = LIB_VERSION_MINOR
VERSION_PATCH = LIB_VERSION_PATCH

del (LIB_VERSION, LIB_VERSION_MAJOR, LIB_VERSION_MINOR, LIB_VERSION_PATCH)

# everything what should have name but has no value, should have value -1
for name in all_names:
    if not name in g:
        g[name] = -1

__all__ = all_names
