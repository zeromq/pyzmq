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

# ZMQ.py is generated from zmq.h using h2py.py
import ZMQ

from ._version import zmq_version_info

g = globals()
for cname, cvalue in ZMQ.__dict__.iteritems():
    if cname.startswith("__"):
        continue
    if cname.startswith("ZMQ_"):
        cname = cname[4:]
    g[cname] = cvalue

# ERRNO.py is generated out of system errno.h using h2py.py
# values in ERRNO overwrite values in ZMQ.py
from .ERRNO import *

VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH = zmq_version_info()
VERSION = "%d%02d%02d" % zmq_version_info()

for name in all_names:
    if not name in g:
        g[name] = -1


__all__ = all_names
