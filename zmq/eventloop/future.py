"""Future-returning Socket for zmq"""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.


import zmq as _zmq
from zmq.eventloop.ioloop import IOLoop

from concurrent.futures import Future


class Socket(_zmq.Socket):
    
    _recv_futures = None
    _send_futures = None
    _state = 0
    _shadow_sock = None
    io_loop = None
    
    def __init__(self, context, socket_type, io_loop=None):
        super(Socket, self).__init__(context, socket_type)
        self.io_loop = io_loop or IOLoop.current()
        self._recv_futures = []
        self._send_futures = []
        self._state = 0
        self._shadow_sock = _zmq.Socket.shadow(self.underlying)
        self._init_io_state()
    
    def recv_multipart(self, flags=0, copy=True, track=False):
        """Recv a multipart message
        
        Returns a Future whose result will be a multipart message.
        """
        f = Future()
        self._recv_futures.append(
            (f, True, dict(flags=flags, copy=copy, track=track))
        )
        self._add_io_state(self.io_loop.READ)
        return f
    
    def recv(self, flags=0, copy=True, track=False):
        f = Future()
        self._recv_futures.append(
            (f, False, dict(flags=flags, copy=copy, track=track))
        )
        self._add_io_state(self.io_loop.READ)
        return f
    
    def _handle_recv(self):
        """Handle recv events"""
        f = None
        while self._recv_futures:
            f, multipart, kwargs = self._recv_futures.pop(0)
            # skip any cancelled futures
            if f.done():
                f = None
            else:
                break
        
        if f is None:
            return
        
        recv = self._shadow_sock.recv_multipart if multipart else self._shadow_sock.recv
        kwargs['flags'] |= _zmq.DONTWAIT
        try:
            result = recv(**kwargs)
        except Exception as e:
            f.set_exception(e)
        else:
            f.set_result(result)
    
    def _handle_send(self):
        pass
    
    # event masking from ZMQStream
    def _handle_events(self, fd, events):
        """Dispatch IO events to _handle_recv, etc."""
        try:
            if events & self.io_loop.READ:
                self._handle_recv()
            if events & self.io_loop.WRITE:
                self._handle_send()
        finally:
            if not self._recv_futures:
                self._drop_io_state(self.io_loop.READ)
            if not self._send_futures:
                self._drop_io_state(self.io_loop.WRITE)
    
    def _add_io_state(self, state):
        """Add io_state to poller."""
        if not self._state & state:
            self._state = self._state | state
            self._update_handler(self._state)
    
    def _drop_io_state(self, state):
        """Stop poller from watching an io_state."""
        if self._state & state:
            self._state = self._state & (~state)
            self._update_handler(self._state)
    
    def _update_handler(self, state):
        """Update IOLoop handler with state."""
        self._state = state
        self.io_loop.update_handler(self, state)
    
    def _init_io_state(self):
        """initialize the ioloop event handler"""
        self.io_loop.add_handler(self, self._handle_events, self._state)
    

class Context(_zmq.Context):
    
    io_loop = None
    @staticmethod
    def _socket_class(self, socket_type):
        return Socket(self, socket_type, io_loop=self.io_loop)
    
    def __init__(self, *args, **kwargs):
        io_loop = kwargs.pop('io_loop', None)
        super(Context, self).__init__(*args, **kwargs)
        self.io_loop = io_loop or IOLoop.current()

    