from ._cffi import C, strerror

class ZMQError(Exception):
    def __init__(self, errno, msg=None):
        if not errno:
            self.errno = C.zmq_errno()
        else:
            self.errno = errno
        if msg:
            self.strerror = msg

    def __str__(self):
        return strerror(self.errno)

class ZMQBindError(Exception):
    pass
