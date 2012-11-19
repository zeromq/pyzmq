from ._cffi import ffi, C, hints
from .error import ZMQError
import codecs

try:
    view = memoryview
except NameError:
    view = buffer

try:
    # below 3.3
    from threading import _Event as Event
except (ImportError):
    from threading import Event

class MessageTracker(object):
    def __init__(self, event):
        self.event = event

class Frame(object):
    def __init__(self, data=None, track=False):
        try:
            data = view(data)
        except TypeError:
            raise

        self.data = data
        self.more = False

        if track:
            evt = Event()
            self.tracker_event = evt
            self.tracker = MessageTracker(evt)
        else:
            self.tracker_event = None
            self.tracker = None

        self.zmq_msg = ffi.new('zmq_msg_t*')

        self.buffer = data
        self.bytes = data

        if data is None:
            rc = C.zmq_msg_init(self.zmq_msg)
            if rc != 0:
                raise ZMQErrror()
            return
        else:
            hint = (data, self.tracker_event)
            hints.append(hint)
            index = len(hints) - 1
            bytes_message = ffi.new('char[]', str(data))
            rc = C.custom_zmq_msg_init(self.zmq_msg,
                                       ffi.cast('void*', bytes_message),
                                       len(data),
                                       ffi.cast('void*', ffi.cast('int', index)))
            if rc != 0:
                raise ZMQErrror()

    def __len__(self):
        return len(self.buffer)

    def __str__(self):
        return self.buffer

    def __eq__(self, other):
        return self.buffer == other

    def decode(self, encoding):
        return codecs.decode(self.data, encoding)
