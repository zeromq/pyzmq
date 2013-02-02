from ._cffi import C, ffi, strerror

def strerror(errno):
    return ffi.buffer(C.zmq_strerror(ffi.cast('int', errno)))[:]

zmq_errno = C.zmq_errno

__all__ = ['strerror', 'zmq_errno']
