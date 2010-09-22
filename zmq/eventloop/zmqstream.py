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

import logging
import time
import zmq
import ioloop
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

class ZMQStream(object):
    """A utility class to register callbacks when a zmq socket sends and receives
    
    For use with zmq.eventloop.ioloop

    There are 3 main methods:
    on_recv(callback,copy=True):
        register a callback to be run every time the socket has something to receive
    on_send(callback):
        register a callback to be run every time you call send
    on_err(callback):
        register a callback to be run every time there is an error
    send(msg, callback=None)
        perform a send that will trigger the callback
        if callback is passed, on_send is also called
        
        There is also send_multipart()
    
    Two other methods for deactivating the callbacks:
    stop_on_recv():
        turn off the recv callback
    stop_on_send():
        turn off the send callback
    stop_on_err():
        turn off the error callback
    
    All of which simply call on_<evt>(None).

    """
    
    socket = None
    io_loop = None
    
    def __init__(self, socket, io_loop=None):
        self.socket = socket
        self.io_loop = io_loop or ioloop.IOLoop.instance()
        
        self._send_queue = Queue()
        self._recv_callback = None
        self._send_callback = None
        self._close_callback = None
        self._errback = None
        self._recv_copy = False
        
        self._state = zmq.POLLERR
        self.io_loop.add_handler(self.socket, self._handle_events, self._state)
        
        # shortcircuit some socket methods
        self.bind = self.socket.bind
        self.connect = self.socket.connect
        self.setsockopt = self.socket.setsockopt
        self.getsockopt = self.socket.getsockopt
    
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
        self._recv_callback = callback
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
        self._send_callback = callback
        if callback is None:
            self._drop_io_state(zmq.POLLOUT)
        else:
            self._add_io_state(zmq.POLLOUT)
        
    def on_err(self, callback):
        """register a callback to be called on POLLERR events
        with no arguments.
        
        Parameters
        ----------
        
        callback : callable
            callback will be passed no arguments.
        """
        # self._add_io_state(zmq.POLLOUT)
        self._errback = callback
        
                
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
    
    def set_close_callback(self, callback):
        """Call the given callback when the stream is closed."""
        self._close_callback = callback

    def close(self):
        """Close this stream."""
        if self.socket is not None:
            self.io_loop.remove_handler(self.socket)
            self.socket.close()
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
            callback(*args, **kwargs)
        except:
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
        if events & zmq.POLLIN:
            self._handle_recv()
        if not self.socket:
            return
        if events & zmq.POLLOUT:
            self._handle_send()
        if not self.socket:
            return
        if events & zmq.POLLERR:
            self._handle_error()
            return
        state = zmq.POLLERR
        if self.receiving():
            state |= zmq.POLLIN
        if self.sending():
            state |= zmq.POLLOUT
        if state != self._state:
            self._state = state
            self.io_loop.update_handler(self.socket, self._state)
            
    def _handle_recv(self):
        """Handle a recv event."""
        try:
            msg = self.socket.recv_multipart(copy=self._recv_copy)
        except zmq.ZMQError:
            logging.error("RECV Error")
        else:
            if self._recv_callback:
                callback = self._recv_callback
                # self._recv_callback = None
                self._run_callback(callback, msg)
                
        # self.update_state()
        

    def _handle_send(self):
        """Handle a send event."""
        if not self.sending():
            return
        
        msg = self._send_queue.get()
        queue = self.socket.send_multipart(*msg)
        if self._send_callback:
            callback = self._send_callback
            self._run_callback(callback, msg, queue)
        
        # unregister from event loop:
        if not self.sending():
            self._drop_io_state(zmq.POLLOUT)
        
        # self.update_state()
    
    def _handle_error(self):
        """Handle a POLLERR event."""
        # if evt & zmq.POLLERR:
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
    

