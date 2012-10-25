from ._cffi import C, strerror

class ZMQError(Exception):
    def __init__(self, errno):
        if not errno:
            self.errno = C.zmq_errno()
        else:
            self.errno = errno

    def __str__(self):
        return strerror(self.errno)

class ZMQBindError(Exception):
    pass
