"""0MQ Socket pure Python methods."""

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
    for i in range(max_tries):
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

    p = zmq.Poller()
    p.register(self, flags)
    evts = dict(p.poll(timeout))
    # return 0 if no events, otherwise return event bitfield
    return evts.get(self, 0)
