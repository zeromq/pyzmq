"""0MQ Socket class."""

#
#    Copyright (c) 2010-2011 Brian E. Granger & Min Ragan-Kelley
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#-----------------------------------------------------------------------------
# Python Imports
#-----------------------------------------------------------------------------

import random
import codecs

import zmq
from zmq.core.basesocket import BaseSocket
from zmq.core import constants
from zmq.core.constants import *
from zmq.core.error import ZMQError, ZMQBindError
from zmq.utils import jsonapi
from zmq.utils.strtypes import bytes,unicode,basestring

try:
    import cPickle
    pickle = cPickle
except:
    cPickle = None
    import pickle

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class Socket(BaseSocket):
    """Socket(context, socket_type)

    A 0MQ socket.

    These objects will generally be constructed via the socket() method of a Context object.
    
    Note: 0MQ Sockets are *not* threadsafe. **DO NOT** share them across threads.
    
    Parameters
    ----------
    context : Context
        The 0MQ Context this Socket belongs to.
    socket_type : int
        The socket type, which can be any of the 0MQ socket types: 
        REQ, REP, PUB, SUB, PAIR, XREQ, DEALER, XREP, ROUTER, PULL, PUSH, XPUB, XSUB.
    
    See Also
    --------
    .Context.socket : method for creating a socket bound to a Context.
    """

    def __new__(cls, *args, **kwargs):
        # need to set _attrs in __new__() so subclasses can create attributes
        # without calling our __init__() first
        socket = super(Socket, cls).__new__(cls, *args, **kwargs)
        super(Socket, socket).__setattr__('_attrs', {})
        return socket
    
    def __init__(self, context, socket_type):
        super(Socket, self).__init__(context, socket_type)

    def __del__(self):
        """close *and* remove from context's list"""
        self.close()
    
    def setsockopt_string(self, option, optval, encoding='utf-8'):
        """s.setsockopt_string(option, optval, encoding='utf-8')

        Set socket options with a unicode object it is simply a wrapper
        for setsockopt to protect from encoding ambiguity.

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
        return self.setsockopt(option, optval.encode(encoding))
    
    def getsockopt_string(self, option, encoding='utf-8'):
        """s.getsockopt_string(option, encoding='utf-8')

        Get the value of a socket option.

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : int
            The option to retrieve. Currently, IDENTITY is the only
            gettable option that can return a string.

        Returns
        -------
        optval : unicode string (unicode on py2, str on py3)
            The value of the option as a unicode string.
        """
        
        if option not in constants.bytes_sockopts:
            raise TypeError("option %i will not return a string to be decoded"%option)
        return self.getsockopt(option).decode(encoding)
    
    setsockopt_unicode = setsockopt_string
    getsockopt_unicode = getsockopt_string

    def __setattr__(self, key, value):
        """set sockopts by attr"""
        try:
            opt = getattr(constants, key.upper())
        except AttributeError:
            # allow subclasses to have extended attributes
            if self.__class__.__module__ != 'zmq.core.socket':
                self._attrs[key] = value
            else:
                raise AttributeError("Socket has no such option: %s"%key.upper())
        else:
            self.setsockopt(opt, value)
    
    def __getattr__(self, key):
        """get sockopts by attr"""
        if key in self._attrs:
            # `key` is subclass extended attribute
            return self._attrs[key]
        key = key.upper()
        try:
            opt = getattr(constants, key)
        except AttributeError:
            raise AttributeError("Socket has no such option: %s"%key)
        else:
            return self.getsockopt(opt)
  
    def bind_to_random_port(self, addr, min_port=49152, max_port=65536, max_tries=100):
        """s.bind_to_random_port(addr, min_port=49152, max_port=65536, max_tries=100)

        Bind this socket to a random port in a range.

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
        for i in xrange(max_tries):
            try:
                port = random.randrange(min_port, max_port)
                self.bind('%s:%s' % (addr, port))
            except ZMQError:
                pass
            else:
                return port
        raise ZMQBindError("Could not bind socket to random port.")

    #-------------------------------------------------------------------------
    # Sending and receiving messages
    #-------------------------------------------------------------------------

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

    send_unicode = send_string
    recv_unicode = recv_string

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

__all__ = ['Socket']
