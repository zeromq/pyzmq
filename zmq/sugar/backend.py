# this will be try/except when other
try:
    from zmq.core import *
    from zmq.core import constants
except ImportError:
    # here will be the cffi backend import, when it exists
    raise
