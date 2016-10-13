"""Future-returning APIs for coroutines."""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.

from collections import namedtuple
from itertools import chain
from zmq import POLLOUT, POLLIN

try:
    from tornado.concurrent import Future
except ImportError:
    from .minitornado.concurrent import Future

class CancelledError(Exception):
    pass

class _TornadoFuture(Future):
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


_FutureEvent = namedtuple('_FutureEvent', ('future', 'kind', 'kwargs', 'msg'))

# mixins for tornado/asyncio compatibility

class _AsyncTornado(object):
    _Future = _TornadoFuture
    _READ = IOLoop.READ
    _WRITE = IOLoop.WRITE
    def _default_loop(self):
        return IOLoop.current()


class _AsyncPoller(_zmq.Poller):
    """Poller that returns a Future on poll, instead of blocking."""

    def poll(self, timeout=-1):
        """Return a Future for a poll event"""
        future = self._Future()
        if timeout == 0:
            try:
                result = super(_AsyncPoller, self).poll(0)
            except Exception as e:
                future.set_exception(e)
            else:
                future.set_result(result)
            return future
        
        loop = self._default_loop()
        
        # register Future to be called as soon as any event is available on any socket
        watcher = self._Future()
        
        # watch raw sockets:
        raw_sockets = []
        def wake_raw(*args):
            if not watcher.done():
                watcher.set_result(None)

        watcher.add_done_callback(lambda f: self._unwatch_raw_sockets(loop, *raw_sockets))

        for socket, mask in self.sockets:
            if isinstance(socket, _AsyncSocket):
                if mask & _zmq.POLLIN:
                    socket._add_recv_event('poll', future=watcher)
                if mask & _zmq.POLLOUT:
                    socket._add_send_event('poll', future=watcher)
            else:
                raw_sockets.append(socket)
                evt = 0
                if mask & _zmq.POLLIN:
                    evt |= self._READ
                if mask & _zmq.POLLOUT:
                    evt |= self._WRITE
                self._watch_raw_socket(loop, socket, evt, wake_raw)
        
        def on_poll_ready(f):
            if future.done():
                return
            if watcher.exception():
                future.set_exception(watcher.exception())
            else:
                try:
                    result = super(_AsyncPoller, self).poll(0)
                except Exception as e:
                    future.set_exception(e)
                else:
                    future.set_result(result)
        watcher.add_done_callback(on_poll_ready)
        
        if timeout is not None and timeout > 0:
            # schedule cancel to fire on poll timeout, if any
            def trigger_timeout():
                if not watcher.done():
                    watcher.set_result(None)
            
            timeout_handle = loop.call_later(
                1e-3 * timeout,
                trigger_timeout
            )
            def cancel_timeout(f):
                if hasattr(timeout_handle, 'cancel'):
                    timeout_handle.cancel()
                else:
                    loop.remove_timeout(timeout_handle)
            future.add_done_callback(cancel_timeout)

        def cancel_watcher(f):
            if not watcher.done():
                watcher.cancel()
        future.add_done_callback(cancel_watcher)

        return future

class Poller(_AsyncTornado, _AsyncPoller):
    def _watch_raw_socket(self, loop, socket, evt, f):
        """Schedule callback for a raw socket"""
        loop.add_handler(socket, lambda *args: f(), evt)

    def _unwatch_raw_sockets(self, loop, *sockets):
        """Unschedule callback for a raw socket"""
        for socket in sockets:
            loop.remove_handler(socket)


class _AsyncSocket(_zmq.Socket):
    
    _recv_futures = None
    _send_futures = None
    _state = 0
    _shadow_sock = None
    _poller_class = Poller
    io_loop = None

    def __init__(self, context, socket_type, io_loop=None):
        super(_AsyncSocket, self).__init__(context, socket_type)
        self.io_loop = io_loop or self._default_loop()
        self._recv_futures = []
        self._send_futures = []
        self._state = 0
        self._shadow_sock = _zmq.Socket.shadow(self.underlying)
        self._init_io_state()

    def close(self, linger=None):
        if not self.closed:
            for event in chain(self._recv_futures, self._send_futures):
                if not event.future.done():
                    event.future.cancel()
            self._clear_io_state()
        super(_AsyncSocket, self).close(linger=linger)
    close.__doc__ = _zmq.Socket.close.__doc__

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
            kwargs=dict(flags=flags, copy=copy, track=track),
        )
    
    def send(self, msg, flags=0, copy=True, track=False):
        """Send a single zmq frame.
        
        Returns a Future that resolves when sending is complete.
        
        Recommend using send_multipart instead.
        """
        return self._add_send_event('send', msg=msg,
            kwargs=dict(flags=flags, copy=copy, track=track),
        )

    def _deserialize(self, recvd, load):
        """Deserialize with Futures"""
        f = self._Future()
        def _chain(_):
            """Chain result through serialization to recvd"""
            if f.done():
                return
            if recvd.exception():
                f.set_exception(recvd.exception())
            else:
                buf = recvd.result()
                try:
                    loaded = load(buf)
                except Exception as e:
                    f.set_exception(e)
                else:
                    f.set_result(loaded)
        recvd.add_done_callback(_chain)

        def _chain_cancel(_):
            """Chain cancellation from f to recvd"""
            if recvd.done():
                return
            if f.cancelled():
                recvd.cancel()
        f.add_done_callback(_chain_cancel)

        return f

    def poll(self, timeout=None, flags=_zmq.POLLIN):
        """poll the socket for events
        
        returns a Future for the poll results.
        """

        if self.closed:
            raise _zmq.ZMQError(_zmq.ENOTSUP)

        p = self._poller_class()
        p.register(self, flags)
        f = p.poll(timeout)
        
        future = self._Future()
        def unwrap_result(f):
            if future.done():
                return
            if f.exception():
                future.set_exception(f.exception())
            else:
                evts = dict(f.result())
                future.set_result(evts.get(self, 0))

        f.add_done_callback(unwrap_result)
        return future

    def _add_timeout(self, future, timeout):
        """Add a timeout for a send or recv Future"""
        def future_timeout():
            if future.done():
                # future already resolved, do nothing
                return

            # pop the entry from _recv_futures
            for f_idx, (f, kind, kwargs, _) in enumerate(self._recv_futures):
                if f == future:
                    self._recv_futures.pop(f_idx)
                    break

            # pop the entry from _send_futures
            for f_idx, (f, kind, kwargs, _) in enumerate(self._send_futures):
                if f == future:
                    self._send_futures.pop(f_idx)
                    break

            # raise EAGAIN
            future.set_exception(_zmq.Again())
        self._call_later(timeout, future_timeout)

    def _call_later(self, delay, callback):
        """Schedule a function to be called later

        Override for different IOLoop implementations

        Tornado and asyncio happen to both have ioloop.call_later
        with the same signature.
        """
        self.io_loop.call_later(delay, callback)

    def _add_recv_event(self, kind, kwargs=None, future=None):
        """Add a recv event, returning the corresponding Future"""
        f = future or self._Future()
        if kind.startswith('recv') and kwargs.get('flags', 0) & _zmq.DONTWAIT:
            # short-circuit non-blocking calls
            recv = getattr(self._shadow_sock, kind)
            try:
                r = recv(**kwargs)
            except Exception as e:
                f.set_exception(e)
            else:
                f.set_result(r)
            return f

        # we add it to the list of futures before we add the timeout as the
        # timeout will remove the future from recv_futures to avoid leaks
        self._recv_futures.append(
            _FutureEvent(f, kind, kwargs, msg=None)
        )

        if hasattr(_zmq, 'RCVTIMEO'):
            timeout_ms = self._shadow_sock.rcvtimeo
            if timeout_ms >= 0:
                self._add_timeout(f, timeout_ms * 1e-3)

        if self.events & POLLIN:
            # recv immediately, if we can
            self._handle_recv()
        if self._recv_futures:
            self._add_io_state(self._READ)
        return f
    
    def _add_send_event(self, kind, msg=None, kwargs=None, future=None):
        """Add a send event, returning the corresponding Future"""
        f = future or self._Future()
        if kind.startswith('send') and kwargs.get('flags', 0) & _zmq.DONTWAIT:
            # short-circuit non-blocking calls
            send = getattr(self._shadow_sock, kind)
            try:
                r = send(msg, **kwargs)
            except Exception as e:
                f.set_exception(e)
            else:
                f.set_result(r)
            return f

        # we add it to the list of futures before we add the timeout as the
        # timeout will remove the future from recv_futures to avoid leaks
        self._send_futures.append(
            _FutureEvent(f, kind, kwargs=kwargs, msg=msg)
        )

        if hasattr(_zmq, 'SNDTIMEO'):
            timeout_ms = self._shadow_sock.sndtimeo
            if timeout_ms >= 0:
                self._add_timeout(f, timeout_ms * 1e-3)

        if self.events & POLLOUT:
            # send immediately if we can
            self._handle_send()
        if self._send_futures:
            self._add_io_state(self._WRITE)
        return f
    
    def _handle_recv(self):
        """Handle recv events"""
        if not self._shadow_sock.events & POLLIN:
            # event triggered, but state may have been changed between trigger and callback
            return
        f = None
        while self._recv_futures:
            f, kind, kwargs, _ = self._recv_futures.pop(0)
            # skip any cancelled futures
            if f.done():
                f = None
            else:
                break
        
        if not self._recv_futures:
            self._drop_io_state(self._READ)
        
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
        if not self._shadow_sock.events & POLLOUT:
            # event triggered, but state may have been changed between trigger and callback
            return
        f = None
        while self._send_futures:
            f, kind, kwargs, msg = self._send_futures.pop(0)
            # skip any cancelled futures
            if f.done():
                f = None
            else:
                break
        
        if not self._send_futures:
            self._drop_io_state(self._WRITE)

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
        if events & self._READ:
            self._handle_recv()
        if events & self._WRITE:
            self._handle_send()
    
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

    def _clear_io_state(self):
        """unregister the ioloop event handler
        
        called once during close
        """
        self.io_loop.remove_handler(self)


class Socket(_AsyncTornado, _AsyncSocket):
    pass

class Context(_zmq.Context):
    
    io_loop = None
    @staticmethod
    def _socket_class(self, socket_type):
        return Socket(self, socket_type, io_loop=self.io_loop)
    
    def __init__(self, *args, **kwargs):
        io_loop = kwargs.pop('io_loop', None)
        super(Context, self).__init__(*args, **kwargs)
        self.io_loop = io_loop or IOLoop.current()

