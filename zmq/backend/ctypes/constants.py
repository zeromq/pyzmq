# coding: utf-8
"""zmq constants"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013-2014 Felipe Cruz, Pawel Jasinski
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

# ERRNO.py is generated out of system errno.h using h2py.py
#
# Standard python errno module (Ironpython 2.7.4) cannot be used, because
# ironpython uses WSA values which do not match posix values. For example:
# errno.EADDRINUSE in ironpython is 10048 which is WSAEADDRINUSE
# errno.EADDRINUSE returned by libzmq is 100

from .ERRNO import *

# extract the actual library version
# TODO: cross check with version of the header used by setup
#       issue warning if mismatch
from ._version import zmq_version_info
VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH = zmq_version_info()
VERSION = "%d%02d%02d" % zmq_version_info()

# everything what should have name but has no value, should have value -1
for name in all_names:
    if not name in g:
        g[name] = -1

__all__ = all_names
