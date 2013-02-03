from ._cffi import C, ffi

def strerror(errno):
    return ffi.string(C.zmq_strerror(errno))

zmq_errno = C.zmq_errno

__all__ = ['strerror', 'zmq_errno']
