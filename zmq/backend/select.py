"""Import basic exposure of libzmq C API as a backend"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

public_api = [
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
    'curve_keypair',
    'constants',
    'zmq_version_info',
    'IPC_PATH_MAX_LEN',
]

def select_backend(name):
    """Select the pyzmq backend"""
    try:
        mod = __import__(name, fromlist=public_api)
    except ImportError:
        raise
    except Exception as e:
        import sys
        from zmq.utils.sixcerpt import reraise
        exc_info = sys.exc_info()
        reraise(ImportError, ImportError("Importing %s failed with %s" % (name, e)), exc_info[2])
    
    ns = {}
    for key in public_api:
        ns[key] = getattr(mod, key)
    return ns
