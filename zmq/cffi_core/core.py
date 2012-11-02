# coding: utf-8

from ._cffi import C, ffi, zmq_version, new_uint64_pointer, \
                                        new_int64_pointer, \
                                        new_int_pointer, \
                                        new_binary_data, \
                                        value_uint64_pointer, \
                                        value_int64_pointer, \
                                        value_int_pointer, \
                                        value_binary_data

from ._cffi import strerror

from .constants import *
from .error import *
from .poll import Poller, _poll

from zmq.utils import jsonapi
import random

_instance = None

class Context(object):
    _state = {}
    def __init__(self, io_threads=1):
        if not io_threads > 0:
            raise ZMQError(EINVAL)

        self.__dict__ = self._state

        self.zmq_ctx = C.zmq_init(io_threads)
        self.iothreads = io_threads
        self._closed = False
        self.n_sockets = 0
        self.max_sockets = 32
        self._sockets = {}
        self.sockopts = {LINGER: 0}
        self.linger = 0

        global _instance
        _instance = self

    def term(self, linger=None):
        if self.closed:
            return

        if zmq_version == 2:
            C.zmq_term(self.zmq_ctx)
        else:
            C.zmq_ctx_destroy(self.zmq_ctx)

        self.zmq_ctx = None
        self._closed = True

    def destroy(self, linger=None):
        if self.closed:
            return

        for k, s in self._sockets.items():
            if not s.closed:
                if linger:
                    s.setsockopt(LINGER, linger)
                elif self.linger:
                    s.setsockopt(LINGER, self.linger)
                s.close()

            del self._sockets[k]

        self.n_sockets = 0

    @classmethod
    def instance(cls, io_threads=1):
        global _instance
        if _instance is None or _instance.closed:
            _instance = cls(io_threads)
        return _instance

    @property
    def closed(self):
        return self._closed

    def _add_socket(self, socket):
        self._sockets[self.n_sockets] = socket
        self.n_sockets += 1

        return self.n_sockets

    def _rm_socket(self, n):
        del self._sockets[n]

    def socket(self, sock_type):
        if self._closed:
            raise ZMQError(ENOTSUP)

        socket = Socket(self, sock_type)
        for option, option_value in self.sockopts.items():
            socket.setsockopt(option, option_value)

        return socket

    def set_linger(self, value):
        self.sockopts[LINGER] = value
        self.linger = value

    def __getattr__(self, attr_name):
        if attr_name == "linger":
            return self.sockopts[LINGER]
        return getattr(self, attr_name)

    def __setattr__(self, attr_name, value):
        if attr_name == "linger":
            self.sockopts[LINGER] = value
        object.__setattr__(self, attr_name, value)

    def __del__(self):
        self.term()

def new_pointer_from_opt(option, length=0):
    if option in uint64_opts:
        return new_uint64_pointer()
    elif option in int64_opts:
        return new_int64_pointer()
    elif option in int_opts:
        return new_int_pointer()
    elif option in binary_opts:
        return new_binary_data(length)
    else:
        raise ValueError('Invalid option')

def value_from_opt_pointer(option, opt_pointer, length=0):
    if option in uint64_opts:
        return int(opt_pointer[0])
    elif option in int64_opts:
        return int(opt_pointer[0])
    elif option in int_opts:
        return int(opt_pointer[0])
    elif option in binary_opts:
        return ffi.string(opt_pointer)
    else:
        raise ValueError('Invalid option')

def initialize_opt_pointer(option, value, length=0):
    if option in uint64_opts:
        return value_uint64_pointer(value)
    elif option in int64_opts:
        return value_int64_pointer(value)
    elif option in int_opts:
        return value_int_pointer(value)
    elif option in binary_opts:
        return value_binary_data(value, length)
    else:
        raise ValueError('Invalid option')


class Socket(object):
    def __init__(self, context, sock_type):
        self.context = context
        self.sock_type = sock_type
        self.zmq_socket = C.zmq_socket(context.zmq_ctx, sock_type)
        if not self.zmq_socket:
            raise ZMQError(EINVAL)
        self._closed = False
        self._attrs = {}
        self.n = self.context._add_socket(self)
        self.last_errno = None
        self.linger = 1

    @property
    def closed(self):
        return self._closed

    def close(self, *args):
        if not self._closed:
            if len(args) == 1:
                self.setsockopt(LINGER, args[0])
            rc = C.zmq_close(self.zmq_socket)
            self._closed = True
            return rc

    def __del__(self):
        self.close()

    def bind(self, address):
        ret = C.zmq_bind(self.zmq_socket, address)
        if ret != 0:
            raise ZMQError()

    def connect(self, address):
        ret = C.zmq_connect(self.zmq_socket, address)
        return ret

    def setsockopt(self, option, value):
        length = None
        if isinstance(value, str):
            length = len(value)
        low_level_data = initialize_opt_pointer(option, value, length)
        low_level_value_pointer = low_level_data[0]
        low_level_sizet = low_level_data[1]
        ret = C.zmq_setsockopt(self.zmq_socket,
                                option,
                                ffi.cast('void*', low_level_value_pointer),
                                low_level_sizet)
        if option == LINGER:
            self.linger = value

        return ret

    def getsockopt(self, option, length=0):
        low_level_data = new_pointer_from_opt(option, length=length)
        low_level_value_pointer = low_level_data[0]
        low_level_sizet_pointer = low_level_data[1]

        ret = C.zmq_getsockopt(self.zmq_socket,
                               option,
                               low_level_value_pointer,
                               low_level_sizet_pointer)

        if ret < 0:
            self.last_errno = C.zmq_errno()
            return -1

        return value_from_opt_pointer(option, low_level_value_pointer)

    def bind_to_random_port(self, addr,
                                  min_port=49152,
                                  max_port=65536,
                                  max_tries=100):
        for i in range(max_tries):
            try:
                port = random.randrange(min_port, max_port)
                self.bind('%s:%s' % (addr, port))
            except ZMQError as exception:
                if not exception.errno == zmq.EADDRINUSE:
                    raise
            else:
                return port
        raise ZMQBindError("Could not bind socket to random port.")

    def send(self, message, flags=0, copy=False):
        zmq_msg = ffi.new('zmq_msg_t*')

        c_message = ffi.new('char[]', message)
        C.zmq_msg_init_size(zmq_msg, len(message))
        C.strncpy(C.zmq_msg_data(zmq_msg), c_message, len(message))

        if zmq_version == 2:
            ret = C.zmq_send(self.zmq_socket, zmq_msg, flags)
        else:
            ret = C.zmq_sendmsg(self. zmq_socket, zmq_msg, flags)

        C.zmq_msg_close(zmq_msg)
        if ret < 0:
            self.last_errno = C.zmq_errno()

        return ret

    def recv(self, flags=0):
        zmq_msg = ffi.new('zmq_msg_t*')
        C.zmq_msg_init(zmq_msg)

        if zmq_version == 2:
            ret = C.zmq_recv(self.zmq_socket, zmq_msg, flags)
        else:
            ret = C.zmq_recvmsg(self.zmq_socket, zmq_msg, flags)

        if ret < 0:
            C.zmq_msg_close(zmq_msg)
            raise ZMQError(C.zmq_errno())

        value = ffi.buffer(C.zmq_msg_data(zmq_msg), int(C.zmq_msg_size(zmq_msg)))[:]

        C.zmq_msg_close(zmq_msg)

        return value

    def send_multipart(self, msg_parts, flags=0, copy=True, track=False):
        """s.send_multipart(msg_parts, flags=0, copy=True, track=False)

        Send a sequence of buffers as a multipart message.

        Parameters
        ----------
        msg_parts : iterable
            A sequence of objects to send as a multipart message. Each element
            can be any sendable object (Frame, bytes, buffer-providers)
        flags : int, optional
            SNDMORE is handled automatically for frames before the last.
        copy : bool, optional
            Should the frame(s) be sent in a copying or non-copying manner.
        track : bool, optional
            Should the frame(s) be tracked for notification that ZMQ has
            finished with it (ignored if copy=True).

        Returns
        -------
        None : if copy or not track
        MessageTracker : if track and not copy
            a MessageTracker object, whose `pending` property will
            be True until the last send is completed.
        """
        for msg in msg_parts[:-1]:
            self.send(msg, SNDMORE|flags, copy=copy, track=track)
        # Send the last part without the extra SNDMORE flag.
        return self.send(msg_parts[-1], flags, copy=copy, track=track)

    def recv_multipart(self, flags=0, copy=True, track=False):
        """s.recv_multipart(flags=0, copy=True, track=False)

        Receive a multipart message as a list of bytes or Frame objects.

        Parameters
        ----------
        flags : int, optional
            Any supported flag: NOBLOCK. If NOBLOCK is set, this method
            will raise a ZMQError with EAGAIN if a message is not ready.
            If NOBLOCK is not set, then this method will block until a
            message arrives.
        copy : bool, optional
            Should the message frame(s) be received in a copying or non-copying manner?
            If False a Frame object is returned for each part, if True a copy of
            the bytes is made for each frame.
        track : bool, optional
            Should the message frame(s) be tracked for notification that ZMQ has
            finished with it? (ignored if copy=True)
        Returns
        -------
        msg_parts : list
            A list of frames in the multipart message; either Frames or bytes,
            depending on `copy`.

        """
        parts = [self.recv(flags, copy=copy, track=track)]
        # have first part already, only loop while more to receive
        while self.getsockopt(zmq.RCVMORE):
            part = self.recv(flags, copy=copy, track=track)
            parts.append(part)

        return parts

    def send_string(self, u, flags=0, copy=False, encoding='utf-8'):
        """s.send_string(u, flags=0, copy=False, encoding='utf-8')

        Send a Python unicode string as a message with an encoding.

        0MQ communicates with raw bytes, so you must encode/decode
        text (unicode on py2, str on py3) around 0MQ.

        Parameters
        ----------
        u : Python unicode string (unicode on py2, str on py3)
            The unicode string to send.
        flags : int, optional
            Any valid send flag.
        encoding : str [default: 'utf-8']
            The encoding to be used
        """
        if not isinstance(u, basestring):
            raise TypeError("unicode/str objects only")
        return self.send(u.encode(encoding), flags=flags, copy=copy)

    def recv_string(self, flags=0, encoding='utf-8'):
        """s.recv_string(flags=0, encoding='utf-8')

        Receive a unicode string, as sent by send_string.

        Parameters
        ----------
        flags : int
            Any valid recv flag.
        encoding : str [default: 'utf-8']
            The encoding to be used

        Returns
        -------
        s : unicode string (unicode on py2, str on py3)
            The Python unicode string that arrives as encoded bytes.
        """
        msg = self.recv(flags=flags, copy=False)
        return codecs.decode(msg.bytes, encoding)


        """s.send_pyobj(obj, flags=0, protocol=-1)

        Send a Python object as a message using pickle to serialize.

        Parameters
        ----------
        obj : Python object
            The Python object to send.
        flags : int
            Any valid send flag.
        protocol : int
            The pickle protocol number to use. Default of -1 will select
            the highest supported number. Use 0 for multiple platform
            support.
        """
        msg = pickle.dumps(obj, protocol)
        return self.send(msg, flags)

    def recv_pyobj(self, flags=0):
        """s.recv_pyobj(flags=0)

        Receive a Python object as a message using pickle to serialize.

        Parameters
        ----------
        flags : int
            Any valid recv flag.

        Returns
        -------
        obj : Python object
            The Python object that arrives as a message.
        """
        s = self.recv(flags)
        return pickle.loads(s)

    def send_json(self, obj, flags=0):
        """s.send_json(obj, flags=0)

        Send a Python object as a message using json to serialize.

        Parameters
        ----------
        obj : Python object
            The Python object to send.
        flags : int
            Any valid send flag.
        """
        if jsonapi.jsonmod is None:
            raise ImportError('jsonlib{1,2}, json or simplejson library is required.')
        else:
            msg = jsonapi.dumps(obj)
            return self.send(msg, flags)

    def recv_json(self, flags=0):
        """s.recv_json(flags=0)

        Receive a Python object as a message using json to serialize.

        Parameters
        ----------
        flags : int
            Any valid recv flag.

        Returns
        -------
        obj : Python object
            The Python object that arrives as a message.
        """
        if jsonapi.jsonmod is None:
            raise ImportError('jsonlib{1,2}, json or simplejson library is required.')
        else:
            msg = self.recv(flags)
            return jsonapi.loads(msg)

    def poll(self, timeout=None, flags=POLLIN):
        """s.poll(timeout=None, flags=POLLIN)

        Poll the socket for events.  The default is to poll forever for incoming
        events.  Timeout is in milliseconds, if specified.

        Parameters
        ----------
        timeout : int [default: None]
            The timeout (in milliseconds) to wait for an event. If unspecified
            (or secified None), will wait forever for an event.
        flags : bitfield (int) [default: POLLIN]
            The event flags to poll for (any combination of POLLIN|POLLOUT).
            The default is to check for incoming events (POLLIN).

        Returns
        -------
        events : bitfield (int)
            The events that are ready and waiting.  Will be 0 if no events were ready
            by the time timeout was reached.
        """

        if self.closed:
            raise ZMQError(ENOTSUP)

        p = zmq.Poller()
        p.register(self, flags)
        evts = dict(p.poll(timeout))
        # return 0 if no events, otherwise return event bitfield
        return evts.get(self, 0)
