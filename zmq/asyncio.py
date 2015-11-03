"""AsyncIO support for zmq

Requires asyncio and Python 3.
"""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.

from functools import partial

import zmq as _zmq
from zmq.eventloop import future as _future

# TODO: support trollius for Legacy Python? (probably not)
import sys
    
import asyncio
from asyncio import SelectorEventLoop, Future
try:
    import selectors
except ImportError:
    from asyncio import selectors # py33


_aio2zmq = {
    selectors.EVENT_READ: _zmq.POLLIN,
    selectors.EVENT_WRITE: _zmq.POLLOUT,
}

_zmq2aio = { z:a for a,z in _aio2zmq.items() }

class _AsyncIO(object):
    _Future = Future
    _WRITE = selectors.EVENT_WRITE
    _READ = selectors.EVENT_READ
    
    def _default_loop(self):
        return asyncio.get_event_loop()


class ZMQSelector(selectors.BaseSelector):
    """zmq_poll-based selector for asyncio"""
    
    def __init__(self):
        self.poller = _zmq.Poller()
        self._mapping = {}
    
    def register(self, fileobj, events, data=None):
        """Register a file object.

        Parameters:
        fileobj -- file object or file descriptor
        events  -- events to monitor (bitwise mask of EVENT_READ|EVENT_WRITE)
        data    -- attached data

        Returns:
        SelectorKey instance

        Raises:
        ValueError if events is invalid
        KeyError if fileobj is already registered
        OSError if fileobj is closed or otherwise is unacceptable to
                the underlying system call (if a system call is made)

        Note:
        OSError may or may not be raised
        """
        if fileobj in self.poller:
            raise KeyError(fileobj)
        if not isinstance(events, int) or events not in _aio2zmq:
            raise ValueError("Invalid events: %r" % events)
        
        self.poller.register(fileobj, _aio2zmq[events])
        key = selectors.SelectorKey(fileobj=fileobj, fd=fileobj if isinstance(fileobj, int) else None, events=events, data=data)
        self._mapping[fileobj] = key
        return key

    def unregister(self, fileobj):
        """Unregister a file object.

        Parameters:
        fileobj -- file object or file descriptor

        Returns:
        SelectorKey instance

        Raises:
        KeyError if fileobj is not registered

        Note:
        If fileobj is registered but has since been closed this does
        *not* raise OSError (even if the wrapped syscall does)
        """
        if fileobj not in self.poller:
            raise KeyError(fileobj)
        
        self.poller.unregister(fileobj)
        return self._mapping.pop(fileobj)

    def select(self, timeout=None):
        """Perform the actual selection, until some monitored file objects are
        ready or a timeout expires.

        Parameters:
        timeout -- if timeout > 0, this specifies the maximum wait time, in
                   seconds
                   if timeout <= 0, the select() call won't block, and will
                   report the currently ready file objects
                   if timeout is None, select() will block until a monitored
                   file object becomes ready

        Returns:
        list of (key, events) for ready file objects
        `events` is a bitwise mask of EVENT_READ|EVENT_WRITE
        """
        if timeout is not None:
            if timeout < 0:
                timeout = 0
            else:
                timeout = 1e3 * timeout
        
        events = self.poller.poll(timeout)
        return [ (self.get_key(fd), _zmq2aio[evt]) for fd, evt in events ]

    def close(self):
        """Close the selector.

        This must be called to make sure that any underlying resource is freed.
        """
        self._mapping = None
        self._poller = None

    def get_map(self):
        """Return a mapping of file objects to selector keys."""
        return self._mapping

class Poller(_AsyncIO, _future._AsyncPoller):
    """Poller returning asyncio.Future for poll results."""
    pass

class Socket(_AsyncIO, _future._AsyncSocket):
    """Socket returning asyncio Futures for send/recv/poll methods."""
    
    _poller_class = Poller

    def _add_io_state(self, state):
        """Add io_state to poller."""
        if not self._state & state:
            self._state = self._state | state
            if state & self._READ:
                self.io_loop.add_reader(self, self._handle_recv)
            if state & self._WRITE:
                self.io_loop.add_writer(self, self._handle_send)
    
    def _drop_io_state(self, state):
        """Stop poller from watching an io_state."""
        if self._state & state:
            self._state = self._state & (~state)
            if state & self._READ:
                self.io_loop.remove_reader(self)
            if state & self._WRITE:
                self.io_loop.remove_writer(self)
    
    def _init_io_state(self):
        """initialize the ioloop event handler"""
        pass

class Context(_zmq.Context):
    """Context for creating asyncio-compatible Sockets"""
    _socket_class = Socket


class ZMQEventLoop(SelectorEventLoop):
    """AsyncIO eventloop using zmq_poll"""
    def __init__(self, selector=None):
        if selector is None:
            selector = ZMQSelector()
        return super(ZMQEventLoop, self).__init__(selector)

_loop = None

def install():
    """Install and return the global ZMQEventLoop
    
    registers the loop with asyncio.set_event_loop
    """
    global _loop
    if _loop is None:
        _loop = ZMQEventLoop()
        asyncio.set_event_loop(_loop)
    return _loop
    

__all__ = [
    'Context',
    'Socket',
    'Poller',
    'ZMQEventLoop',
    'install',
]