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
    'proxy',
    'zmq_poll',
    'strerror',
    'zmq_errno',
    'constants',
    'zmq_version_info',
    'constants',
    'IPC_PATH_MAX_LEN',
] + constants.__all__
