# coding: utf-8

from ._cffi import C, ffi, zmq_version_info, new_uint64_pointer, \
                                             new_int64_pointer, \
                                             new_int_pointer, \
                                             new_binary_data, \
                                             value_uint64_pointer, \
                                             value_int64_pointer, \
                                             value_int_pointer, \
                                             value_binary_data, \
                                             zmq_major_version, \
                                             IPC_PATH_MAX_LEN

from ._cffi import strerror
from .constants import *
from .error import *
from ._poll import Poller, _poll
from .message import Frame

import cPickle as pickle
from zmq.utils import jsonapi
import random
import codecs

import errno as errno_mod

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
        return ffi.buffer(opt_pointer, length)[:]
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
        self.__dict__['context'] = context
        self.__dict__['socket_type'] = sock_type
        self.__dict__['zmq_socket'] = C.zmq_socket(context.zmq_ctx, sock_type)
        if not self.zmq_socket:
            raise ZMQError(C.zmq_errno())
        self.__dict__['_closed'] = False
        self.__dict__['_attrs'] = {}
        self.__dict__['n'] = self.context._add_socket(self)
        self.__dict__['last_errno'] = None
        self.__dict__['rcvmore'] = False

    @property
    def closed(self):
        return self._closed

    def close(self, *args):
        if not self._closed:
            rc = C.zmq_close(self.zmq_socket)
            self.__dict__['_closed'] = True
            return rc

    def __del__(self):
        self.close()

    def bind(self, addr):
        ret = C.zmq_bind(self.zmq_socket, addr)
        if ret != 0:
            if IPC_PATH_MAX_LEN and C.zmq_errno() == errno_mod.ENAMETOOLONG:
                # py3compat: addr is bytes, but msg wants str
                if str is unicode:
                    addr = addr.decode('utf-8', 'replace')
                path = addr.split('://', 1)[-1]
                msg = ('ipc path "{0}" is longer than {1} '
                                'characters (sizeof(sockaddr_un.sun_path)).'
                                .format(path, IPC_PATH_MAX_LEN))
                raise ZMQError(C.zmq_errno(), msg=msg)
            else:
                raise ZMQError(C.zmq_errno())

    def connect(self, address):
        ret = C.zmq_connect(self.zmq_socket, address)
        if ret != 0:
            raise ZMQError(C.zmq_errno())
        return ret

    def __getattr__(self, key):
        """get sockopts by attr"""
        if key in self._attrs:
            # `key` is subclass extended attribute
            return self._attrs[key]
        key = key.upper()
        if key == 'HWM':
            return self.get_hwm()
        try:
            opt = constants[key]
        except KeyError:
            raise AttributeError("Socket has no such option: %s"%key)
        else:
            return self.getsockopt(opt)

    def __setattr__(self, key, value):
        """set sockopts by attr"""
        key = key
        upper_key = key.upper()
        if upper_key == "HWM":
            self.set_hwm(value)
            return
        try:
            opt = constants[upper_key]
        except KeyError:
            # allow subclasses to have extended attributes
            if not self.__class__.__module__ in ('zmq.core.socket',
                                                 'zmq.cffi_core.socket'):
                self._attrs[key] = value
            else:
                raise AttributeError("Socket has no such option: %s" % upper_key)
        else:
            self.setsockopt(opt, value)

    def get_hwm(self):
        if zmq_version_info()[0] == 2:
            return self.getsockopt(HWM)
        else:
            return self.getsockopt(SNDHWM)

    def set_hwm(self, value):
        if zmq_version_info()[0] == 2:
            self.setsockopt(HWM, value)
        else:
            self.setsockopt(SNDHWM, value)
            self.setsockopt(RCVHWM, value)

    def setsockopt(self, option, value):
        length = None
        str_value = False

        if isinstance(value, str):
            length = len(value)
            str_value = True

        try:
            low_level_data = initialize_opt_pointer(option, value, length)
        except ValueError:
            if not str_value:
                raise ZMQError(EINVAL)
            raise TypeError("Invalid Option")

        low_level_value_pointer = low_level_data[0]
        low_level_sizet = low_level_data[1]

        ret = C.zmq_setsockopt(self.zmq_socket,
                               option,
                               ffi.cast('void*', low_level_value_pointer),
                               low_level_sizet)
        if ret < 0:
            raise ZMQError(C.zmq_errno())

        self._attrs[option] = value

        return ret

    def getsockopt(self, option, length=0):
        if option in bytes_sockopts:
            length = 255

        try:
            low_level_data = new_pointer_from_opt(option, length=length)
        except ValueError:
            raise ZMQError(EINVAL)

        low_level_value_pointer = low_level_data[0]
        low_level_sizet_pointer = low_level_data[1]

        ret = C.zmq_getsockopt(self.zmq_socket,
                               option,
                               low_level_value_pointer,
                               low_level_sizet_pointer)

        if ret < 0:
            raise ZMQError(C.zmq_errno())

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
                raise exception
            else:
                return port
        raise ZMQBindError("Could not bind socket to random port.")

    def send(self, message, flags=0, copy=False, track=False):
        if bytes == str and isinstance(message, unicode):
            raise TypeError("Message must be in bytes, not an unicode Object")

        zmq_msg = ffi.new('zmq_msg_t*')

        c_message = ffi.new('char[]', message)
        C.zmq_msg_init_size(zmq_msg, len(message))
        C.memcpy(C.zmq_msg_data(zmq_msg), c_message, len(message))

        if zmq_version_info()[0] == 2:
            ret = C.zmq_send(self.zmq_socket, zmq_msg, flags)
        else:
            ret = C.zmq_sendmsg(self.zmq_socket, zmq_msg, flags)

        C.zmq_msg_close(zmq_msg)
        if ret < 0:
            raise ZMQError(C.zmq_errno())

        return ret

    def recv(self, flags=0, copy=True, track=False):
        zmq_msg = ffi.new('zmq_msg_t*')
        C.zmq_msg_init(zmq_msg)

        if zmq_version_info()[0] == 2:
            ret = C.zmq_recv(self.zmq_socket, zmq_msg, flags)
        else:
            ret = C.zmq_recvmsg(self.zmq_socket, zmq_msg, flags)

        if ret < 0:
            C.zmq_msg_close(zmq_msg)
            raise ZMQError(C.zmq_errno())

        self.__dict__['rcvmore'] = self.getsockopt(RCVMORE)

        value = ffi.buffer(C.zmq_msg_data(zmq_msg), int(C.zmq_msg_size(zmq_msg)))[:]

        C.zmq_msg_close(zmq_msg)

        return Frame(data=value)

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
        while self.getsockopt(RCVMORE):
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


    def send_pyobj(self, obj, flags=0, protocol=-1):
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

        p = Poller()
        p.register(self, flags=flags)
        evts = dict(p.poll(timeout))
        # return 0 if no events, otherwise return event bitfield
        return evts.get(self, 0)



def send_string(self, u, flags=0, copy=False, encoding='utf-8'):
    if not isinstance(u, basestring):
        raise TypeError("unicode/str objects only")
    return self.send(u.encode(encoding), flags=flags, copy=copy)

def recv_string(self, flags=0, encoding='utf-8'):
    msg = self.recv(flags=flags, copy=False)
    return codecs.decode(msg.bytes, encoding)

def setsockopt_string(self, option, optval, encoding='utf-8'):
    if not isinstance(optval, unicode):
        raise TypeError("unicode strings only")
    return self.setsockopt(option, optval.encode(encoding))

def getsockopt_string(self, option, encoding='utf-8'):
    if option not in bytes_sockopts:
        raise TypeError("option %i will not return a string to be decoded"%option)
    return self.getsockopt(option).decode(encoding)

if str == unicode: #py3k
    Socket.send_string = send_string
    Socket.recv_string = recv_string
    Socket.getsockopt_string = getsockopt_string
    Socket.setsockopt_string = setsockopt_string
else:
    Socket.send_unicode = send_string
    Socket.recv_unicode = recv_string
    Socket.getsockopt_unicode = getsockopt_string
    Socket.setsockopt_unicode = setsockopt_string
