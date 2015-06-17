# coding: utf-8
"""0MQ Socket pure Python methods."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import errno
import random
import sys
import warnings

import zmq
from zmq.backend import Socket as SocketBase
from .poll import Poller
from . import constants
from .attrsettr import AttributeSetter
from zmq.error import ZMQError, ZMQBindError
from zmq.utils import jsonapi
from zmq.utils.strtypes import bytes,unicode,basestring
from zmq.utils.interop import cast_int_addr

from .constants import (
    SNDMORE, ENOTSUP, POLLIN,
    int64_sockopt_names,
    int_sockopt_names,
    bytes_sockopt_names,
    fd_sockopt_names,
)
try:
    import cPickle
    pickle = cPickle
except:
    cPickle = None
    import pickle

try:
    DEFAULT_PROTOCOL = pickle.DEFAULT_PROTOCOL
except AttributeError:
    DEFAULT_PROTOCOL = pickle.HIGHEST_PROTOCOL

try:
    _buffer_type = memoryview
except NameError:
    _buffer_type = buffer

class Socket(SocketBase, AttributeSetter):
    """The ZMQ socket object
    
    To create a Socket, first create a Context::
    
        ctx = zmq.Context.instance()
    
    then call ``ctx.socket(socket_type)``::
    
        s = ctx.socket(zmq.ROUTER)
    
    """
    _shadow = False
    
    def __init__(self, *a, **kw):
        super(Socket, self).__init__(*a, **kw)
        if 'shadow' in kw:
            self._shadow = True
        else:
            self._shadow = False
    
    def __del__(self):
        if not self._shadow:
            self.close()
    
    # socket as context manager:
    def __enter__(self):
        """Sockets are context managers
        
        .. versionadded:: 14.4
        """
        return self
    
    def __exit__(self, *args, **kwargs):
        self.close()
    
    #-------------------------------------------------------------------------
    # Socket creation
    #-------------------------------------------------------------------------
    
    def __copy__(self, memo=None):
        """Copying a Socket creates a shadow copy"""
        return self.__class__.shadow(self.underlying)
    
    __deepcopy__ = __copy__
    
    @classmethod
    def shadow(cls, address):
        """Shadow an existing libzmq socket
        
        address is the integer address of the libzmq socket
        or an FFI pointer to it.
        
        .. versionadded:: 14.1
        """
        address = cast_int_addr(address)
        return cls(shadow=address)
    
    #-------------------------------------------------------------------------
    # Deprecated aliases
    #-------------------------------------------------------------------------
    
    @property
    def socket_type(self):
        warnings.warn("Socket.socket_type is deprecated, use Socket.type",
            DeprecationWarning
        )
        return self.type
    
    #-------------------------------------------------------------------------
    # Hooks for sockopt completion
    #-------------------------------------------------------------------------
    
    def __dir__(self):
        keys = dir(self.__class__)
        for collection in (
            bytes_sockopt_names,
            int_sockopt_names,
            int64_sockopt_names,
            fd_sockopt_names,
        ):
            keys.extend(collection)
        return keys
    
    #-------------------------------------------------------------------------
    # Getting/Setting options
    #-------------------------------------------------------------------------
    setsockopt = SocketBase.set
    getsockopt = SocketBase.get
    
    def set_string(self, option, optval, encoding='utf-8'):
        """set socket options with a unicode object
        
        This is simply a wrapper for setsockopt to protect from encoding ambiguity.

        See the 0MQ documentation for details on specific options.
        
        Parameters
        ----------
        option : int
            The name of the option to set. Can be any of: SUBSCRIBE, 
            UNSUBSCRIBE, IDENTITY
        optval : unicode string (unicode on py2, str on py3)
            The value of the option to set.
        encoding : str
            The encoding to be used, default is utf8
        """
        if not isinstance(optval, unicode):
            raise TypeError("unicode strings only")
        return self.set(option, optval.encode(encoding))
    
    setsockopt_unicode = setsockopt_string = set_string
    
    def get_string(self, option, encoding='utf-8'):
        """get the value of a socket option

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : int
            The option to retrieve.

        Returns
        -------
        optval : unicode string (unicode on py2, str on py3)
            The value of the option as a unicode string.
        """
    
        if option not in constants.bytes_sockopts:
            raise TypeError("option %i will not return a string to be decoded"%option)
        return self.getsockopt(option).decode(encoding)
    
    getsockopt_unicode = getsockopt_string = get_string
    
    def bind_to_random_port(self, addr, min_port=49152, max_port=65536, max_tries=100):
        """bind this socket to a random port in a range

        If the port range is unspecified, the system will choose the port.

        Parameters
        ----------
        addr : str
            The address string without the port to pass to ``Socket.bind()``.
        min_port : int, optional
            The minimum port in the range of ports to try (inclusive).
        max_port : int, optional
            The maximum port in the range of ports to try (exclusive).
        max_tries : int, optional
            The maximum number of bind attempts to make.

        Returns
        -------
        port : int
            The port the socket was bound to.
    
        Raises
        ------
        ZMQBindError
            if `max_tries` reached before successful bind
        """
        if hasattr(constants, 'LAST_ENDPOINT') and min_port == 49152 and max_port == 65536:
            # if LAST_ENDPOINT is supported, and min_port / max_port weren't specified,
            # we can bind to port 0 and let the OS do the work
            self.bind("%s:0" % addr)
            url = self.last_endpoint.decode('ascii', 'replace')
            _, port_s = url.rsplit(':', 1)
            return int(port_s)
        
        for i in range(max_tries):
            try:
                port = random.randrange(min_port, max_port)
                self.bind('%s:%s' % (addr, port))
            except ZMQError as exception:
                en = exception.errno
                if en == zmq.EADDRINUSE:
                    continue
                elif sys.platform == 'win32' and en == errno.EACCES:
                    continue
                else:
                    raise
            else:
                return port
        raise ZMQBindError("Could not bind socket to random port.")
    
    def get_hwm(self):
        """get the High Water Mark
        
        On libzmq ≥ 3, this gets SNDHWM if available, otherwise RCVHWM
        """
        major = zmq.zmq_version_info()[0]
        if major >= 3:
            # return sndhwm, fallback on rcvhwm
            try:
                return self.getsockopt(zmq.SNDHWM)
            except zmq.ZMQError as e:
                pass
            
            return self.getsockopt(zmq.RCVHWM)
        else:
            return self.getsockopt(zmq.HWM)
    
    def set_hwm(self, value):
        """set the High Water Mark
        
        On libzmq ≥ 3, this sets both SNDHWM and RCVHWM


        .. warning::

            New values only take effect for subsequent socket
            bind/connects.
        """
        major = zmq.zmq_version_info()[0]
        if major >= 3:
            raised = None
            try:
                self.sndhwm = value
            except Exception as e:
                raised = e
            try:
                self.rcvhwm = value
            except Exception as e:
                raised = e
            
            if raised:
                raise raised
        else:
            return self.setsockopt(zmq.HWM, value)
    
    hwm = property(get_hwm, set_hwm,
        """property for High Water Mark
        
        Setting hwm sets both SNDHWM and RCVHWM as appropriate.
        It gets SNDHWM if available, otherwise RCVHWM.
        """
    )
    
    #-------------------------------------------------------------------------
    # Sending and receiving messages
    #-------------------------------------------------------------------------

    def send_multipart(self, msg_parts, flags=0, copy=True, track=False):
        """send a sequence of buffers as a multipart message
        
        The zmq.SNDMORE flag is added to all msg parts before the last.

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
        # typecheck parts before sending:
        for i,msg in enumerate(msg_parts):
            if isinstance(msg, (zmq.Frame, bytes, _buffer_type)):
                continue
            try:
                _buffer_type(msg)
            except Exception as e:
                rmsg = repr(msg)
                if len(rmsg) > 32:
                    rmsg = rmsg[:32] + '...'
                raise TypeError(
                    "Frame %i (%s) does not support the buffer interface." % (
                    i, rmsg,
                ))
        for msg in msg_parts[:-1]:
            self.send(msg, SNDMORE|flags, copy=copy, track=track)
        # Send the last part without the extra SNDMORE flag.
        return self.send(msg_parts[-1], flags, copy=copy, track=track)

    def recv_multipart(self, flags=0, copy=True, track=False):
        """receive a multipart message as a list of bytes or Frame objects

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

    def send_string(self, u, flags=0, copy=True, encoding='utf-8'):
        """send a Python unicode string as a message with an encoding
    
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
    
    send_unicode = send_string
    
    def recv_string(self, flags=0, encoding='utf-8'):
        """receive a unicode string, as sent by send_string
    
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
        b = self.recv(flags=flags)
        return b.decode(encoding)
    
    recv_unicode = recv_string
    
    def send_pyobj(self, obj, flags=0, protocol=DEFAULT_PROTOCOL):
        """send a Python object as a message using pickle to serialize

        Parameters
        ----------
        obj : Python object
            The Python object to send.
        flags : int
            Any valid send flag.
        protocol : int
            The pickle protocol number to use. The default is pickle.DEFAULT_PROTOCOL
            where defined, and pickle.HIGHEST_PROTOCOL elsewhere.
        """
        msg = pickle.dumps(obj, protocol)
        return self.send(msg, flags)

    def recv_pyobj(self, flags=0):
        """receive a Python object as a message using pickle to serialize

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

    def send_json(self, obj, flags=0, **kwargs):
        """send a Python object as a message using json to serialize
        
        Keyword arguments are passed on to json.dumps
        
        Parameters
        ----------
        obj : Python object
            The Python object to send
        flags : int
            Any valid send flag
        """
        msg = jsonapi.dumps(obj, **kwargs)
        return self.send(msg, flags)

    def recv_json(self, flags=0, **kwargs):
        """receive a Python object as a message using json to serialize

        Keyword arguments are passed on to json.loads
        
        Parameters
        ----------
        flags : int
            Any valid recv flag.

        Returns
        -------
        obj : Python object
            The Python object that arrives as a message.
        """
        msg = self.recv(flags)
        return jsonapi.loads(msg, **kwargs)
    
    _poller_class = Poller

    def poll(self, timeout=None, flags=POLLIN):
        """poll the socket for events
        
        The default is to poll forever for incoming
        events.  Timeout is in milliseconds, if specified.

        Parameters
        ----------
        timeout : int [default: None]
            The timeout (in milliseconds) to wait for an event. If unspecified
            (or specified None), will wait forever for an event.
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

        p = self._poller_class()
        p.register(self, flags)
        evts = dict(p.poll(timeout))
        # return 0 if no events, otherwise return event bitfield
        return evts.get(self, 0)

    def get_monitor_socket(self, events=None, addr=None):
        """Return a connected PAIR socket ready to receive the event notifications.
        
        .. versionadded:: libzmq-4.0
        .. versionadded:: 14.0
        
        Parameters
        ----------
        events : bitfield (int) [default: ZMQ_EVENTS_ALL]
            The bitmask defining which events are wanted.
        addr :  string [default: None]
            The optional endpoint for the monitoring sockets.

        Returns
        -------
        socket :  (PAIR)
            The socket is already connected and ready to receive messages.
        """
        # safe-guard, method only available on libzmq >= 4
        if zmq.zmq_version_info() < (4,):
            raise NotImplementedError("get_monitor_socket requires libzmq >= 4, have %s" % zmq.zmq_version())
        if addr is None:
            # create endpoint name from internal fd
            addr = "inproc://monitor.s-%d" % self.FD
        if events is None:
            # use all events
            events = zmq.EVENT_ALL
        # attach monitoring socket
        self.monitor(addr, events)
        # create new PAIR socket and connect it
        ret = self.context.socket(zmq.PAIR)
        ret.connect(addr)
        return ret

    def disable_monitor(self):
        """Shutdown the PAIR socket (created using get_monitor_socket)
        that is serving socket events.
        
        .. versionadded:: 14.4
        """
        self.monitor(None, 0)


__all__ = ['Socket']
