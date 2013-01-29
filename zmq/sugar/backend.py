"""Import basic exposure of libzmq C API as a backend"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# this will be try/except when other
try:
    from zmq.core import (
        Context,
        Socket, IPC_PATH_MAX_LEN,
        Frame, Message,
        Stopwatch,
        device, proxy,
        strerror, zmq_errno,
        zmq_poll,
        zmq_version_info,
        constants,
    )
except ImportError:
    from zmq.cffi_core import (
        Context,
        Socket, IPC_PATH_MAX_LEN,
        Frame, Message,
        Stopwatch,
        device, proxy,
        strerror, zmq_errno,
        zmq_poll,
        zmq_version_info,
        constants,
    )

__all__ = [
    'Context',
    'Socket',
    'Frame',
    'Message',
    'Stopwatch',
    'device',
    'proxy',
    'zmq_poll',
    'strerror',
    'zmq_errno',
    'constants',
    'zmq_version_info',
    'IPC_PATH_MAX_LEN',
]
