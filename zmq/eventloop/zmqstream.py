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

# import errno
# import socket
import logging
import time
import zmq
import ioloop

class ZMQStream(object):
    """A utility class to register callbacks when a zmq socket sends and receives
    
    For use with zmq.eventloop.ioloop

    There are 3 main methods:
    on_recv(callback):
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

    """
    
    socket = None
    io_loop = None
    
    def __init__(self, socket, io_loop=None):
        self.socket = socket
        self.io_loop = io_loop or ioloop.IOLoop.instance()
        self._tosend = None
        # self._recv_buffer = ""
        # self._send_buffer = ""
        self._recv_callback = None
        self._send_callback = None
        self._close_callback = None
        self._errback = None
        self._state = zmq.POLLERR
        self.io_loop.add_handler(self.socket, self._handle_events, self._state)
        
        # shortcircuit some socket methods
        self.bind = self.socket.bind
        self.connect = self.socket.connect
    
    def stop_on_recv(self):
        """disable callback and automatic receiving"""
        self._recv_callback = None
        self._drop_io_state(zmq.POLLIN)
    
    def stop_on_send(self):
        """disable callback on sending"""
        self._send_callback = None
        self._drop_io_state(zmq.POLLOUT)
    
    def stop_on_err(self):
        self._errback = None
        # self._drop_io_state(zmq.POLLOUT)
    
    def on_recv(self, callback):
        """register a callback to be called on each recv.
        callback must take exactly one argument, which will be a
        list, returned by socket.recv_multipart()."""
        # assert not self._recv_callback, "Already receiving"
        self._recv_callback = callback
        self._add_io_state(zmq.POLLIN)
    
    def on_send(self, callback):
        """register a callback to be called on each send
        with no arguments (?)
        """
        self._add_io_state(zmq.POLLOUT)
        self._send_callback = callback
        
    def on_err(self, callback):
        """register a callback to be called on each send
        with no arguments (?)
        """
        # self._add_io_state(zmq.POLLOUT)
        self._errback = callback
        
                
    def send(self, msg, callback=None):
        """send a message, optionally also register
        """
        return self.send_multipart([msg], callback=callback)

    def send_multipart(self, msg, callback=None):
        """send a multipart message
        """
        # self._check_closed()
        self._tosend = msg
        callback = callback or self._send_callback
        if callback is not None:
            self.on_send(callback)
        else:
            self.on_send(lambda : None)
    
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
        """Returns true if we are currently receiving from the stream."""
        return self._recv_callback is not None

    def sending(self):
        """Returns true if we are currently sending to the stream."""
        return self._tosend is not None

    def closed(self):
        return self.socket is None

    def _run_callback(self, callback, *args, **kwargs):
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
        if self._tosend is not None:
            state |= zmq.POLLOUT
        if state != self._state:
            self._state = state
            self.io_loop.update_handler(self.socket, self._state)
            
    def _handle_recv(self):
        # print "handling recv"
        try:
            msg = self.socket.recv_multipart()
        except zmq.ZMQError:
            logging.warning("RECV Error")
        else:
            if self._recv_callback:
                callback = self._recv_callback
                # self._recv_callback = None
                self._run_callback(callback, msg)
                
        # self.update_state()
        

    def _handle_send(self):
        # print "handling send"
        if not self._tosend:
            return
        self.socket.send_multipart(self._tosend)
        self._tosend = None
        if self._send_callback:
            callback = self._send_callback
            self._run_callback(callback)
        
        # unregister from event loop:
        self._drop_io_state(zmq.POLLOUT)
        
        # self.update_state()
    
    def _handle_error(self):
        # if evt & zmq.POLLERR:
        logging.warning("handling error..")
        if self._errback is not None:
            self._errback()
        else:
            raise zmq.ZMQError()


        # raise zmq.ZMQError()

    def _check_closed(self):
        if not self.socket:
            raise IOError("Stream is closed")

    def _add_io_state(self, state):
        if not self._state & state:
            self._state = self._state | state
            self.io_loop.update_handler(self.socket, self._state)
    
    def _drop_io_state(self, state):
        if self._state & state:
            self._state = self._state & (~state)
            self.io_loop.update_handler(self.socket, self._state)
    

