#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A utility class to send to and recv from a non-blocking socket."""

from __future__ import with_statement

import sys
import logging

import zmq
from zmq.core.socket import jsonapi, pickle

from zmq.eventloop import ioloop
from zmq.eventloop import stack_context

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from zmq.utils.strtypes import bytes, unicode, basestring

try:
    callable
except NameError:
    callable = lambda obj: hasattr(obj, '__call__')


class ZMQStream(object):
    """A utility class to register callbacks when a zmq socket sends and receives
    
    For use with zmq.eventloop.ioloop

    There are 4 main methods
    
    Methods:
    
    * **on_recv(callback,copy=True):**
        register a callback to be run every time the socket has something to receive
    * **on_send(callback):**
        register a callback to be run every time you call send
    * **on_err(callback):**
        register a callback to be run every time there is an error
    * **send(self, msg, flags=0, copy=False, callback=None):**
        perform a send that will trigger the callback
        if callback is passed, on_send is also called
        
        There are also send_multipart(), send_json(), send_pyobj()
    
    Three other methods for deactivating the callbacks:
    
    * **stop_on_recv():**
        turn off the recv callback
    * **stop_on_send():**
        turn off the send callback
    * **stop_on_err():**
        turn off the error callback
    
    All of which simply call ``on_<evt>(None)``.
    
    The entire socket interface, excluding direct recv methods, is also
    provided, primarily through direct-linking the methods.
    e.g.
    
    >>> stream.bind is stream.socket.bind
    True
    
    """
    
    socket = None
    io_loop = None
    poller = None
    
    def __init__(self, socket, io_loop=None):
        self.socket = socket
        self.io_loop = io_loop or ioloop.IOLoop.instance()
        self.poller = zmq.Poller()
        
        self._send_queue = Queue()
        self._recv_callback = None
        self._send_callback = None
        self._close_callback = None
        self._errback = None
        self._recv_copy = False
        self._flushed = False
        
        self._state = zmq.POLLERR
        with stack_context.NullContext():
            self.io_loop.add_handler(
                self.socket, self._handle_events, self._state)
        
        # shortcircuit some socket methods
        self.bind = self.socket.bind
        self.bind_to_random_port = self.socket.bind_to_random_port
        self.connect = self.socket.connect
        self.setsockopt = self.socket.setsockopt
        self.getsockopt = self.socket.getsockopt
        self.setsockopt_unicode = self.socket.setsockopt_unicode
        self.getsockopt_unicode = self.socket.getsockopt_unicode
    
    
    def stop_on_recv(self):
        """Disable callback and automatic receiving."""
        return self.on_recv(None)
    
    def stop_on_send(self):
        """Disable callback on sending."""
        return self.on_send(None)
    
    def stop_on_err(self):
        """Disable callback on errors."""
        return self.on_err(None)
    
    def on_recv(self, callback, copy=True):
        """Register a callback to be called when a message is ready to recv.
        There can be only one callback registered at a time, so each
        call to on_recv replaces previously registered callbacks.
        
        on_recv(None) disables recv event polling.
        
        Parameters
        ----------
        
        callback : callable
            callback must take exactly one argument, which will be a
            list, as returned by socket.recv_multipart()
            if callback is None, recv callbacks are disabled.
        copy : bool
            copy is passed directly to recv, so if copy is False,
            callback will receive Message objects. If copy is True,
            then callback will receive bytes/str objects.
        
        Returns : None
        """
        
        assert callback is None or callable(callback)
        self._recv_callback = stack_context.wrap(callback)
        self._recv_copy = copy
        if callback is None:
            self._drop_io_state(zmq.POLLIN)
        else:
            self._add_io_state(zmq.POLLIN)
    
    def on_send(self, callback):
        """Register a callback to be called on each send
        There will be two arguments: the message being sent (always a list), 
        and the return result of socket.send_multipart(msg).
        
        Non-copying sends return a MessageTracker object whose
        `done` attribute will be True when the send is complete. 
        This allows users to track when an object is safe to write to
        again.
        
        The second argument will always be None if copy=True
        on the send.
        
        on_send(None) disables recv event polling.
        
        Parameters
        ----------
        
        callback : callable
            callback must take exactly two arguments, which will be
            There will be two arguments: the message being sent (always a list), 
            and the return result of socket.send_multipart(msg) - 
            MessageTracker or None.
            
            if callback is None, send callbacks are disabled.
        """
        assert callback is None or callable(callback)
        self._send_callback = stack_context.wrap(callback)
        
    def on_err(self, callback):
        """register a callback to be called on POLLERR events
        with no arguments.
        
        Parameters
        ----------
        
        callback : callable
            callback will be passed no arguments.
        """
        assert callback is None or callable(callback)
        self._errback = stack_context.wrap(callback)
        
                
    def send(self, msg, flags=0, copy=False, callback=None):
        """Send a message, optionally also register a new callback for sends.
        See zmq.socket.send for details.
        """
        return self.send_multipart([msg], flags=flags, copy=copy, callback=callback)

    def send_multipart(self, msg, flags=0, copy=False, callback=None):
        """Send a multipart message, optionally also register a new callback for sends.
        See zmq.socket.send_multipart for details.
        """
        # self._check_closed()
        self._send_queue.put((msg, flags, copy))
        callback = callback or self._send_callback
        if callback is not None:
            self.on_send(callback)
        else:
            # noop callback
            self.on_send(lambda *args: None)
        self._add_io_state(zmq.POLLOUT)
    
    def send_unicode(self, u, flags=0, encoding='utf-8', callback=None):
        """Send a unicode message with an encoding.
        See zmq.socket.send_unicode for details.
        """
        if not isinstance(u, basestring):
            raise TypeError("unicode/str objects only")
        return self.send(u.encode(encoding), flags=flags, callback=callback)

    def send_json(self, obj, flags=0, callback=None):
        """Send json-serialized version of an object.
        See zmq.socket.send_json for details.
        """
        if jsonapi is None:
            raise ImportError('jsonlib{1,2}, json or simplejson library is required.')
        else:
            msg = jsonapi.dumps(obj)
            return self.send(msg, flags=flags, callback=callback)

    def send_pyobj(self, obj, flags=0, protocol=-1, callback=None):
        """Send a Python object as a message using pickle to serialize.

        See zmq.socket.send_json for details.
        """
        msg = pickle.dumps(obj, protocol)
        return self.send(msg, flags, callback=callback)
    
    def _finish_flush(self):
        """callback for unsetting _flushed flag."""
        self._flushed = False
    
    def flush(self, flag=zmq.POLLIN|zmq.POLLOUT, limit=None):
        """Flush pending messages.

        This method safely handles all pending incoming and/or outgoing messages,
        bypassing the inner loop, passing them to the registered callbacks.

        A limit can be specified, to prevent blocking under high load.

        flush will return the first time ANY of these conditions are met:
            * No more events matching the flag are pending.
            * the total number of events handled reaches the limit.

        Note that if ``flag|POLLIN != 0``, recv events will be flushed even if no callback
        is registered, unlike normal IOLoop operation. This allows flush to be
        used to remove *and ignore* incoming messages.

        Parameters
        ----------
        flag : int, default=POLLIN|POLLOUT
                0MQ poll flags.
                If flag|POLLIN,  recv events will be flushed.
                If flag|POLLOUT, send events will be flushed.
                Both flags can be set at once, which is the default.
        limit : None or int, optional
                The maximum number of messages to send or receive.
                Both send and recv count against this limit.

        Returns
        -------
        int : count of events handled (both send and recv)
        """
        # unset self._flushed, so callbacks will execute, in case flush has
        # already been called this iteration
        already_flushed = self._flushed
        self._flushed = False
        # initialize counters
        count = 0
        def update_flag():
            """Update the poll flag, to prevent registering POLLOUT events
            if we don't have pending sends."""
            return flag & zmq.POLLIN | (self.sending() and flag & zmq.POLLOUT)
        flag = update_flag()
        if not flag:
            # nothing to do
            return 0
        self.poller.register(self.socket, flag)
        events = self.poller.poll(0)
        while events and (not limit or count < limit):
            s,event = events[0]
            if event & zmq.POLLIN: # receiving
                self._handle_recv()
                count += 1
            if event & zmq.POLLOUT and self.sending():
                self._handle_send()
                count += 1
            
            flag = update_flag()
            if flag:
                self.poller.register(self.socket, flag)
                events = self.poller.poll(0)
            else:
                events = []
        if count: # only bypass loop if we actually flushed something
            # skip send/recv callbacks this iteration
            self._flushed = True
            # reregister them at the end of the loop
            if not already_flushed: # don't need to do it again
                dc = ioloop.DelayedCallback(self._finish_flush, 0, self.io_loop)
                dc.start()
        elif already_flushed:
            self._flushed = True
        return count
    
    def set_close_callback(self, callback):
        """Call the given callback when the stream is closed."""
        self._close_callback = stack_context.wrap(callback)
    
    def close(self):
        """Close this stream."""
        if self.socket is not None:
            self.io_loop.remove_handler(self.socket)
            dc = ioloop.DelayedCallback(self.socket.close, 100, self.io_loop)
            dc.start()
            self.socket = None
            if self._close_callback:
                self._run_callback(self._close_callback)

    def receiving(self):
        """Returns True if we are currently receiving from the stream."""
        return self._recv_callback is not None

    def sending(self):
        """Returns True if we are currently sending to the stream."""
        return not self._send_queue.empty()

    def closed(self):
        return self.socket is None

    def _run_callback(self, callback, *args, **kwargs):
        """Wrap running callbacks in try/except to allow us to
        close our socket."""
        try:
            # Use a NullContext to ensure that all StackContexts are run
            # inside our blanket exception handler rather than outside.
            with stack_context.NullContext():
                callback(*args, **kwargs)
        except:
            logging.error("Uncaught exception, closing connection.",
                          exc_info=True)
            # Close the socket on an uncaught exception from a user callback
            # (It would eventually get closed when the socket object is
            # gc'd, but we don't want to rely on gc happening before we
            # run out of file descriptors)
            self.close()
            # Re-raise the exception so that IOLoop.handle_callback_exception
            # can see it and log the error
            raise

    def _handle_events(self, fd, events):
        """This method is the actual handler for IOLoop, that gets called whenever
        an event on my socket is posted. It dispatches to _handle_recv, etc."""
        # print "handling events"
        if not self.socket:
            logging.warning("Got events for closed stream %s", fd)
            return
        try:
            # dispatch events:
            if events & zmq.POLLERR:
                self._handle_error()
                return
            if events & zmq.POLLIN:
                self._handle_recv()
                if not self.socket:
                    return
            if events & zmq.POLLOUT:
                self._handle_send()
                if not self.socket:
                    return

            # rebuild the poll state
            state = zmq.POLLERR
            if self.receiving():
                state |= zmq.POLLIN
            if self.sending():
                state |= zmq.POLLOUT
            if state != self._state:
                self._state = state
                self.io_loop.update_handler(self.socket, self._state)
        except:
            logging.error("Uncaught exception, closing connection.",
                          exc_info=True)
            self.close()
            raise
            
    def _handle_recv(self):
        """Handle a recv event."""
        if self._flushed:
            return
        try:
            msg = self.socket.recv_multipart(zmq.NOBLOCK, copy=self._recv_copy)
        except zmq.ZMQError:
            e = sys.exc_info()[1]
            if e.errno == zmq.EAGAIN:
                # state changed since poll event
                pass
            else:
                logging.error("RECV Error: %s"%zmq.strerror(e.errno))
        else:
            if self._recv_callback:
                callback = self._recv_callback
                # self._recv_callback = None
                self._run_callback(callback, msg)
                
        # self.update_state()
        

    def _handle_send(self):
        """Handle a send event."""
        if self._flushed:
            return
        if not self.sending():
            logging.error("Shouldn't have handled a send event")
            return
        
        msg = self._send_queue.get()
        try:
            status = self.socket.send_multipart(*msg)
        except zmq.ZMQError:
            e = sys.exc_info()[1]
            status = e
        if self._send_callback:
            callback = self._send_callback
            self._run_callback(callback, msg, status)
        
        # self.update_state()
    
    def _handle_error(self):
        """Handle a POLLERR event."""
        logging.error("handling error..")
        if self._errback is not None:
            self._errback()
        else:
            raise zmq.ZMQError()

    def _check_closed(self):
        if not self.socket:
            raise IOError("Stream is closed")

    def _add_io_state(self, state):
        """Add io_state to poller."""
        if not self._state & state:
            self._state = self._state | state
            self.io_loop.update_handler(self.socket, self._state)
    
    def _drop_io_state(self, state):
        """Stop poller from watching an io_state."""
        if self._state & state:
            self._state = self._state & (~state)
            self.io_loop.update_handler(self.socket, self._state)
    

