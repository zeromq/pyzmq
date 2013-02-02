from ._cffi import ffi, C
import codecs
import time

try:
    view = memoryview
except NameError:
    view = buffer

try:
    # below 3.3
    from threading import _Event as Event
except (ImportError):
    from threading import Event

_content = lambda x: x.tobytes() if type(x) == memoryview else x

class Frame(object):
    def __init__(self, data, zmq_msg=None, track=False):
        try:
            view(data)
        except TypeError:
            raise

        self.data = data

        if isinstance(data, unicode):
            raise TypeError("Unicode objects not allowed. Only: str/bytes, " +
                            "buffer interfaces.")

        self.more = False
        self.tracker = None
        self.closed = False

        rc = 0
        if data is None:
            self.zmq_msg = ffi.new('zmq_msg_t*')
            rc = C.zmq_msg_init(self.zmq_msg)
        elif data is not None and zmq_msg is not None:
            self.zmq_msg = zmq_msg
        else:
            self.zmq_msg = ffi.new('zmq_msg_t*')
            cffi_data = ffi.new('char[]', _content(data))
            data_len = len(cffi_data)
            rc = C.zmq_msg_init_size(self.zmq_msg, data_len)
            C.memcpy(C.zmq_msg_data(self.zmq_msg), cffi_data, data_len)

        self.buffer = view(self.bytes)

        if rc != 0:
            raise ZMQErrror()

    @property
    def bytes(self):
        data = _content(self.data)
        return data

    def __len__(self):
        return len(self.bytes)

    def __eq__(self, other):
        return self.bytes == _content(other)

    def __str__(self):
        return str(self.bytes)

    def __repr__(self):
        return str(self.bytes)

    def __del__(self):
        C.zmq_msg_close(self.zmq_msg)

    def decode(self, encoding):
        return codecs.decode(self.data, encoding)

    @property
    def done(self):
        return True

Message = Frame

__all__ = ['Frame', 'Message']
