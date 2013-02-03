"""CFFI backend (for PyPY)"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Felipe Cruz
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from zmq.cffi_core import (constants, error, message, context, socket,
                           _poll, devices, stopwatch)

__all__ = []
for submod in (constants, error, message, context, socket,
               _poll, devices, stopwatch):
    __all__.extend(submod.__all__)

from zmq.cffi_core.constants import *
from zmq.cffi_core.error import *
from zmq.cffi_core.message import *
from zmq.cffi_core.context import *
from zmq.cffi_core.socket import *
from zmq.cffi_core.devices import *
from zmq.cffi_core._poll import *
from ._cffi import zmq_version_info
from zmq.cffi_core.stopwatch import *
