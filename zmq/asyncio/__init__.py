"""AsyncIO support for zmq

Requires asyncio and Python 3.
"""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.
# Derived from Python 3.5.1 selectors._BaseSelectorImpl, used under PSF License

from collections import Mapping

import zmq as _zmq
from zmq.eventloop import future as _future

# TODO: support trollius for Legacy Python? (probably not)

import asyncio
from asyncio import SelectorEventLoop, Future
try:
    import selectors
except ImportError:
    from asyncio import selectors # py33


_aio2zmq_map = {
    selectors.EVENT_READ: _zmq.POLLIN,
    selectors.EVENT_WRITE: _zmq.POLLOUT,
}

_AIO_EVENTS = 0
for aio_evt in _aio2zmq_map:
    _AIO_EVENTS |= aio_evt

def _aio2zmq(aio_evt):
    """Turn AsyncIO event mask into ZMQ event mask"""
    z_evt = 0
    for aio_mask, z_mask in _aio2zmq_map.items():
        if aio_mask & aio_evt:
            z_evt |= z_mask
    return z_evt

def _zmq2aio(z_evt):
    """Turn ZMQ event mask into AsyncIO event mask"""
    aio_evt = 0
    for aio_mask, z_mask in _aio2zmq_map.items():
        if z_mask & z_evt:
            aio_evt |= aio_mask
    return aio_evt


class _AsyncIO(object):
    _Future = Future
    _WRITE = selectors.EVENT_WRITE
    _READ = selectors.EVENT_READ

    def _default_loop(self):
        return asyncio.get_event_loop()


def _fileobj_to_fd(fileobj):
    """Return a file descriptor from a file object.

    Parameters:
    fileobj -- file object or file descriptor

    Returns:
    corresponding file descriptor

    Raises:
    ValueError if the object is invalid
    """
    if isinstance(fileobj, int):
        fd = fileobj
    else:
        try:
            fd = int(fileobj.fileno())
        except (AttributeError, TypeError, ValueError):
            raise ValueError("Invalid file object: "
                             "{!r}".format(fileobj)) from None
    if fd < 0:
        raise ValueError("Invalid file descriptor: {}".format(fd))
    return fd


class _SelectorMapping(Mapping):
    """Mapping of file objects to selector keys."""

    def __init__(self, selector):
        self._selector = selector

    def __len__(self):
        return len(self._selector._fd_to_key)

    def __getitem__(self, fileobj):
        try:
            fd = self._selector._fileobj_lookup(fileobj)
            return self._selector._fd_to_key[fd]
        except KeyError:
            raise KeyError("{!r} is not registered".format(fileobj)) from None

    def __iter__(self):
        return iter(self._selector._fd_to_key)


class ZMQSelector(selectors.BaseSelector):
    """zmq_poll-based selector for asyncio"""

    def __init__(self):
        super().__init__()
        # this maps file descriptors to keys
        self._fd_to_key = {}
        # read-only mapping returned by get_map()
        self._map = _SelectorMapping(self)
        self._zmq_poller = _zmq.Poller()

    def _fileobj_lookup(self, fileobj):
        """Return a zmq socket or a file descriptor from a file object.

        This wraps _fileobj_to_fd() to do an exhaustive search in case
        the object is invalid but we still have it in our map.  This
        is used by unregister() so we can unregister an object that
        was previously registered even if it is closed.  It is also
        used by _SelectorMapping.
        """
        if isinstance(fileobj, _zmq.Socket):
            return fileobj
        else:
            try:
                return _fileobj_to_fd(fileobj)
            except ValueError:
                # Do an exhaustive search.
                for key in self._fd_to_key.values():
                    if key.fileobj is fileobj:
                        return key.fd
                # Raise ValueError after all.
                raise

    def register(self, fileobj, events, data=None):
        """Register a file object.

        Parameters:
        fileobj -- zmq socket, file object or file descriptor
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
        if (not events) or (events & ~(selectors.EVENT_READ | selectors.EVENT_WRITE)):
            raise ValueError("Invalid events: {!r}".format(events))

        key = selectors.SelectorKey(fileobj, self._fileobj_lookup(fileobj), events, data)

        if key.fd in self._fd_to_key:
            raise KeyError("{!r} (FD {}) is already registered"
                           .format(fileobj, key.fd))

        self._fd_to_key[key.fd] = key

        self._zmq_poller.register(key.fd, _aio2zmq(events))
        return key

    def unregister(self, fileobj):
        """Unregister a file object.

        Parameters:
        fileobj -- zmq socket, file object or file descriptor

        Returns:
        SelectorKey instance

        Raises:
        KeyError if fileobj is not registered

        Note:
        If fileobj is registered but has since been closed this does
        *not* raise OSError (even if the wrapped syscall does)
        """
        try:
            key = self._fd_to_key.pop(self._fileobj_lookup(fileobj))
        except KeyError:
            raise KeyError("{!r} is not registered".format(fileobj)) from None

        self._zmq_poller.unregister(key.fd)
        return key

    def modify(self, fileobj, events, data=None):
        try:
            key = self._fd_to_key[self._fileobj_lookup(fileobj)]
        except KeyError:
            raise KeyError("{!r} is not registered".format(fileobj)) from None
        if events != key.events:
            self.unregister(fileobj)
            key = self.register(fileobj, events, data)
        elif data != key.data:
            # Use a shortcut to update the data.
            key = key._replace(data=data)
            self._fd_to_key[key.fd] = key
        return key

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

        fd_event_list = self._zmq_poller.poll(timeout)
        ready = []
        for fd, event in fd_event_list:
            key = self._key_from_fd(fd)
            if key:
                events = _zmq2aio(event)
                ready.append((key, events))
        return ready

    def close(self):
        """Close the selector.

        This must be called to make sure that any underlying resource is freed.
        """
        self._fd_to_key.clear()
        self._map = None
        self._zmq_poller = None

    def get_map(self):
        return self._map

    def _key_from_fd(self, fd):
        """Return the key associated to a given file descriptor.

        Parameters:
        fd -- file descriptor

        Returns:
        corresponding key, or None if not found
        """
        try:
            return self._fd_to_key[fd]
        except KeyError:
            return None


class Poller(_AsyncIO, _future._AsyncPoller):
    """Poller returning asyncio.Future for poll results."""
    def _watch_raw_socket(self, loop, socket, evt, f):
        """Schedule callback for a raw socket"""
        if evt & self._READ:
            loop.add_reader(socket, lambda *args: f())
        if evt & self._WRITE:
            loop.add_writer(socket, lambda *args: f())

    def _unwatch_raw_sockets(self, loop, *sockets):
        """Unschedule callback for a raw socket"""
        for socket in sockets:
            loop.remove_reader(socket)
            loop.remove_writer(socket)


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

    def _clear_io_state(self):
        """clear any ioloop event handler

        called once at close
        """
        self._drop_io_state(self._state)

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
