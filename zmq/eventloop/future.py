"""Future-returning APIs for coroutines."""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.

from collections import namedtuple

try:
    from concurrent.futures import Future
except:
    from tornado.concurrent import Future as TFuture
    
    class CancelledError(Exception):
        pass
    
    class Future(TFuture):
        """Subclass Tornado Future, reinstating cancellation."""
        def cancel(self):
            if self.done():
                return False
            self.set_exception(CancelledError())
            return True
        
        def cancelled(self):
            return self.done() and isinstance(self.exception(), CancelledError)

import zmq as _zmq
from zmq.eventloop.ioloop import IOLoop


_FutureEvent = namedtuple('_FutureEvent', ('future', 'kind', 'args', 'msg'))


class Poller(_zmq.Poller):
    """Poller that returns a Future on poll, instead of blocking."""
    def poll(self, timeout=-1):
        """Return a Future for a poll event"""
        future = Future()
        if timeout == 0:
            try:
                result = super(Poller, self).poll(0)
            except Exception as e:
                future.set_exception(e)
            else:
                future.set_result(result)
            return future
        
        loop = IOLoop.current()
        
        # register Future to be called as soon as any event is available on any socket
        # only support polling on zmq sockets, for now
        watcher = Future()
        for socket, mask in self.sockets:
            if mask & _zmq.POLLIN:
                socket._add_recv_event('poll', future=watcher)
            if mask & _zmq.POLLOUT:
                socket._add_send_event('poll', future=watcher)
        
        def on_poll_ready(f):
            if future.done():
                return
            if watcher.exception():
                future.set_exception(watcher.exception())
            else:
                try:
                    result = super(Poller, self).poll(0)
                except Exception as e:
                    future.set_exception(e)
                else:
                    future.set_result(result)
        watcher.add_done_callback(on_poll_ready)
        
        if timeout > 0:
            # schedule cancel to fire on poll timeout, if any
            def trigger_timeout():
                if not watcher.done():
                    watcher.set_result(None)
            
            timeout_handle = loop.call_later(
                1e-3 * timeout,
                trigger_timeout
            )
            def cancel_timeout(f):
                loop.remove_timeout(timeout_handle)
            future.add_done_callback(cancel_timeout)
        
        def cancel_watcher(f):
            if not watcher.done():
                watcher.cancel()
        future.add_done_callback(cancel_watcher)
            
        return future


class Socket(_zmq.Socket):
    
    _recv_futures = None
    _send_futures = None
    _state = 0
    _shadow_sock = None
    _poller_class = Poller
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
        """Receive a complete multipart zmq message.
        
        Returns a Future whose result will be a multipart message.
        """
        return self._add_recv_event('recv_multipart',
            dict(flags=flags, copy=copy, track=track)
        )
    
    def recv(self, flags=0, copy=True, track=False):
        """Receive a single zmq frame.
        
        Returns a Future, whose result will be the received frame.
        
        Recommend using recv_multipart instead.
        """
        return self._add_recv_event('recv',
            dict(flags=flags, copy=copy, track=track)
        )
    
    def send_multipart(self, msg, flags=0, copy=True, track=False):
        """Send a complete multipart zmq message.
        
        Returns a Future that resolves when sending is complete.
        """
        return self._add_send_event('send_multipart', msg=msg,
            args=dict(flags=flags, copy=copy, track=track),
        )
    
    def send(self, msg, flags=0, copy=True, track=False):
        """Send a single zmq frame.
        
        Returns a Future that resolves when sending is complete.
        
        Recommend using send_multipart instead.
        """
        return self._add_send_event('send', msg=msg,
            args=dict(flags=flags, copy=copy, track=track),
        )
    
    def poll(self, timeout=None, flags=_zmq.POLLIN):
        """poll the socket for events
        
        returns a Future for the poll results.
        """

        if self.closed:
            raise _zmq.ZMQError(_zmq.ENOTSUP)

        p = self._poller_class()
        p.register(self, flags)
        f = p.poll(timeout)
        
        future = Future()
        def unwrap_result(f):
            if future.done():
                return
            if f.exception():
                future.set_exception(f.exeception())
            else:
                evts = dict(f.result())
                future.set_result(evts.get(self, 0))
        
        f.add_done_callback(unwrap_result)
        return future

    def _add_recv_event(self, kind, args=None, future=None):
        """Add a recv event, returning the corresponding Future"""
        f = future or Future()
        self._recv_futures.append(
            _FutureEvent(f, kind, args, msg=None)
        )
        self._add_io_state(self.io_loop.READ)
        return f
    
    def _add_send_event(self, kind, msg=None, args=None, future=None):
        """Add a recv event, returning the corresponding Future"""
        f = future or Future()
        self._send_futures.append(
            _FutureEvent(f, kind, args=args, msg=msg)
        )
        self._add_io_state(self.io_loop.WRITE)
        return f
    
    def _handle_recv(self):
        """Handle recv events"""
        f = None
        while self._recv_futures:
            f, kind, kwargs, _ = self._recv_futures.pop(0)
            # skip any cancelled futures
            if f.done():
                f = None
            else:
                break
        
        if f is None:
            return
        
        if kind == 'poll':
            # on poll event, just signal ready, nothing else.
            f.set_result(None)
            return
        elif kind == 'recv_multipart':
            recv = self._shadow_sock.recv_multipart
        elif kind == 'recv':
            recv = self._shadow_sock.recv
        else:
            raise ValueError("Unhandled recv event type: %r" % kind)
        
        kwargs['flags'] |= _zmq.DONTWAIT
        try:
            result = recv(**kwargs)
        except Exception as e:
            f.set_exception(e)
        else:
            f.set_result(result)
    
    def _handle_send(self):
        f = None
        while self._send_futures:
            f, kind, kwargs, msg = self._send_futures.pop(0)
            # skip any cancelled futures
            if f.done():
                f = None
            else:
                break
        
        if f is None:
            return
        
        if kind == 'poll':
            # on poll event, just signal ready, nothing else.
            f.set_result(None)
            return
        elif kind == 'send_multipart':
            send = self._shadow_sock.send_multipart
        elif kind == 'send':
            send = self._shadow_sock.send
        else:
            raise ValueError("Unhandled send event type: %r" % kind)
        
        kwargs['flags'] |= _zmq.DONTWAIT
        try:
            result = send(msg, **kwargs)
        except Exception as e:
            f.set_exception(e)
        else:
            f.set_result(result)
    
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

