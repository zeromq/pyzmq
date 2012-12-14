from ._cffi import ffi, C, hints
from .error import ZMQError, NotDone
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

class MessageTracker(object):
    def __init__(self, *towatch):
        """MessageTracker(*towatch)

        Create a message tracker to track a set of mesages.

        Parameters
        ----------
        *towatch : tuple of Event, MessageTracker, Message instances.
            This list of objects to track. This class can track the low-level
            Events used by the Message class, other MessageTrackers or
            actual Messages.
        """
        self.events = set()
        self.peers = set()
        for obj in towatch:
            if isinstance(obj, Event):
                self.events.add(obj)
            elif isinstance(obj, MessageTracker):
                self.peers.add(obj)
            elif isinstance(obj, Frame):
                if not obj.tracker:
                    raise ValueError("Not a tracked message")
                self.peers.add(obj.tracker)
            else:
                raise TypeError("Require Events or Message Frames, not %s"%type(obj))

    @property
    def done(self):
        """Is 0MQ completely done with the message(s) being tracked?"""
        for evt in self.events:
            if not evt.is_set():
                return False
        for pm in self.peers:
            if not pm.done:
                return False
        return True

    def wait(self, timeout=-1):
        """mt.wait(timeout=-1)

        Wait for 0MQ to be done with the message or until `timeout`.

        Parameters
        ----------
        timeout : float [default: -1, wait forever]
            Maximum time in (s) to wait before raising NotDone.

        Returns
        -------
        None
            if done before `timeout`

        Raises
        ------
        NotDone
            if `timeout` reached before I am done.
        """
        tic = time.time()
        if timeout is False or timeout < 0:
            remaining = 3600*24*7 # a week
        else:
            remaining = timeout
        done = False
        for evt in self.events:
            if remaining < 0:
                raise NotDone
            evt.wait(timeout=remaining)
            if not evt.is_set():
                raise NotDone
            toc = time.time()
            remaining -= (toc-tic)
            tic = toc

        for peer in self.peers:
            if remaining < 0:
                raise NotDone
            peer.wait(timeout=remaining)
            toc = time.time()
            remaining -= (toc-tic)
            tic = toc

    def old_wait(self):
        """If the new wait works, remove this method."""
        while not self.done:
            time.sleep(.001)


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
            hint = (data, self.tracker)
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
        if type(self.buffer) == memoryview:
            return self.buffer.tobytes()[:]
        return self.buffer

    def __eq__(self, other):
        return str(self) == other

    def decode(self, encoding):
        return codecs.decode(self.data, encoding)
