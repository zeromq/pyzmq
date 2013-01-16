# this will be try/except when other
try:
    from zmq.core import (
        Context,
        Socket,
        Frame, Message,
        zmq_poll,
        strerror, zmq_errno,
        constants,
        Stopwatch,
        zmq_version_info,
        device,
        IPC_PATH_MAX_LEN,
    )
    from zmq.core import constants
    from zmq.core.constants import *
except ImportError:
    # here will be the cffi backend import, when it exists
    raise

__all__ = [
    'Context',
    'Socket',
    'Frame',
    'Message',
    'Stopwatch',
    'device',
    'zmq_poll',
    'strerror',
    'zmq_errno',
    'constants',
    'zmq_version_info',
    'constants',
    'IPC_PATH_MAX_LEN',
] + constants.__all__
