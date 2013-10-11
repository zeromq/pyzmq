"""CFFI backend (for PyPY)"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from zmq.backend.cffi import (constants, error, message, context, socket,
                           _poll, devices, utils)

__all__ = []
for submod in (constants, error, message, context, socket,
               _poll, devices, utils):
    __all__.extend(submod.__all__)

from .constants import *
from .error import *
from .message import *
from .context import *
from .socket import *
from .devices import *
from ._poll import *
from ._cffi import zmq_version_info, ffi
from .utils import *
