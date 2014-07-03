from libc.errno cimport EINTR, EAGAIN
from cpython cimport PyErr_CheckSignals
from libzmq cimport zmq_errno, ZMQ_ETERM

cdef inline int _check_rc(int rc) except -1:
    """internal utility for checking zmq return condition
    
    and raising the appropriate Exception class
    """
    cdef int errno = zmq_errno()
    PyErr_CheckSignals()
    if rc < 0:
        if errno == EAGAIN:
            try:
                from zmq.error import Again
            except TypeError:
                return 0
            raise Again(errno)
        elif errno == ZMQ_ETERM:
            try:
                from zmq.error import ContextTerminated
            except TypeError:
                return 0
            raise ContextTerminated(errno)
        else:
            try:
                from zmq.error import ZMQError
            except TypeError:
                return 0
            raise ZMQError(errno)
        # return -1
    return 0
