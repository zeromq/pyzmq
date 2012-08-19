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

"""An I/O event loop for non-blocking sockets.

Typical applications will use a single `IOLoop` object, in the
`IOLoop.instance` singleton.  The `IOLoop.start` method should usually
be called at the end of the ``main()`` function.  Atypical applications may
use more than one `IOLoop`, such as one `IOLoop` per thread, or per `unittest`
case.

In addition to I/O events, the `IOLoop` can also schedule time-based events.
`IOLoop.add_timeout` is a non-blocking alternative to `time.sleep`.
"""

from __future__ import absolute_import, division, with_statement

import datetime
import errno
import heapq
import os
import sys
import logging
import threading
import time
import traceback

try:
    import thread
except ImportError:
    # py3k removed thread
    thread_get_ident = lambda : threading.current_thread().ident
else:
    thread_get_ident = thread.get_ident

from zmq.eventloop import stack_context

try:
    import signal
except ImportError:
    signal = None

from zmq.eventloop.platform.auto import set_close_exec, Waker

from zmq import (
    Poller,
    POLLIN, POLLOUT, POLLERR,
    ZMQError, ETERM,
)

if sys.version_info[0] >= 3:
    # all ints are long in py3k
    long = int

class IOLoop(object):
    """A level-triggered I/O loop.

    We use the zmq Poller for polling events.
    
    Example usage for a simple TCP server::

        import errno
        import functools
        import ioloop
        import socket

        def connection_ready(sock, fd, events):
            while True:
                try:
                    connection, address = sock.accept()
                except socket.error, e:
                    if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                        raise
                    return
                connection.setblocking(0)
                handle_connection(connection, address)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        sock.bind(("", port))
        sock.listen(128)

        io_loop = ioloop.IOLoop.instance()
        callback = functools.partial(connection_ready, sock)
        io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
        io_loop.start()

    """
    # Constants from the epoll module
    _EPOLLIN = 0x001
    _EPOLLPRI = 0x002
    _EPOLLOUT = 0x004
    _EPOLLERR = 0x008
    _EPOLLHUP = 0x010
    _EPOLLRDHUP = 0x2000
    _EPOLLONESHOT = (1 << 30)
    _EPOLLET = (1 << 31)

    # Our events map exactly to the epoll events
    NONE = 0
    READ = _EPOLLIN
    WRITE = _EPOLLOUT
    ERROR = _EPOLLERR | _EPOLLHUP

    # Global lock for creating global IOLoop instance
    _instance_lock = threading.Lock()

    def __init__(self, impl=None):
        self._impl = impl or _poll()
        if hasattr(self._impl, 'fileno'):
            set_close_exec(self._impl.fileno())
        self._handlers = {}
        self._events = {}
        self._callbacks = []
        self._callback_lock = threading.Lock()
        self._timeouts = []
        self._running = False
        self._stopped = False
        self._thread_ident = None
        self._blocking_signal_threshold = None

        # Create a pipe that we send bogus data to when we want to wake
        # the I/O loop when it is idle
        self._waker = Waker()
        self.add_handler(self._waker.fileno(),
                         lambda fd, events: self._waker.consume(),
                         self.READ)

    @staticmethod
    def instance():
        """Returns a global IOLoop instance.

        Most single-threaded applications have a single, global IOLoop.
        Use this method instead of passing around IOLoop instances
        throughout your code.

        A common pattern for classes that depend on IOLoops is to use
        a default argument to enable programs with multiple IOLoops
        but not require the argument for simpler applications::

            class MyClass(object):
                def __init__(self, io_loop=None):
                    self.io_loop = io_loop or IOLoop.instance()
        """
        if not hasattr(IOLoop, "_instance"):
            with IOLoop._instance_lock:
                if not hasattr(IOLoop, "_instance"):
                    # New instance after double check
                    IOLoop._instance = IOLoop()
        return IOLoop._instance

    @staticmethod
    def initialized():
        """Returns true if the singleton instance has been created."""
        return hasattr(IOLoop, "_instance")

    def install(self):
        """Installs this IOloop object as the singleton instance.

        This is normally not necessary as `instance()` will create
        an IOLoop on demand, but you may want to call `install` to use
        a custom subclass of IOLoop.
        """
        assert not IOLoop.initialized()
        IOLoop._instance = self

    def close(self, all_fds=False):
        """Closes the IOLoop, freeing any resources used.

        If ``all_fds`` is true, all file descriptors registered on the
        IOLoop will be closed (not just the ones created by the IOLoop itself).

        Many applications will only use a single IOLoop that runs for the
        entire lifetime of the process.  In that case closing the IOLoop
        is not necessary since everything will be cleaned up when the
        process exits.  `IOLoop.close` is provided mainly for scenarios
        such as unit tests, which create and destroy a large number of
        IOLoops.

        An IOLoop must be completely stopped before it can be closed.  This
        means that `IOLoop.stop()` must be called *and* `IOLoop.start()` must
        be allowed to return before attempting to call `IOLoop.close()`.
        Therefore the call to `close` will usually appear just after
        the call to `start` rather than near the call to `stop`.
        """
        self.remove_handler(self._waker.fileno())
        if all_fds:
            for fd in self._handlers.keys()[:]:
                try:
                    if hasattr(fd, 'close'):
                        fd.close()
                    else:
                        os.close(fd)
                except Exception:
                    logging.debug("error closing fd %s", fd, exc_info=True)
        self._waker.close()
        self._impl.close()

    def add_handler(self, fd, handler, events):
        """Registers the given handler to receive the given events for fd."""
        self._handlers[fd] = stack_context.wrap(handler)
        self._impl.register(fd, events | self.ERROR)

    def update_handler(self, fd, events):
        """Changes the events we listen for fd."""
        self._impl.modify(fd, events | self.ERROR)

    def remove_handler(self, fd):
        """Stop listening for events on fd."""
        self._handlers.pop(fd, None)
        self._events.pop(fd, None)
        try:
            self._impl.unregister(fd)
        except (OSError, IOError):
            logging.debug("Error deleting fd from IOLoop", exc_info=True)

    def set_blocking_signal_threshold(self, seconds, action):
        """Sends a signal if the ioloop is blocked for more than s seconds.

        Pass seconds=None to disable.  Requires python 2.6 on a unixy
        platform.

        The action parameter is a python signal handler.  Read the
        documentation for the python 'signal' module for more information.
        If action is None, the process will be killed if it is blocked for
        too long.
        """
        if not hasattr(signal, "setitimer"):
            logging.error("set_blocking_signal_threshold requires a signal module "
                       "with the setitimer method")
            return
        self._blocking_signal_threshold = seconds
        if seconds is not None:
            signal.signal(signal.SIGALRM,
                          action if action is not None else signal.SIG_DFL)

    def set_blocking_log_threshold(self, seconds):
        """Logs a stack trace if the ioloop is blocked for more than s seconds.
        Equivalent to set_blocking_signal_threshold(seconds, self.log_stack)
        """
        self.set_blocking_signal_threshold(seconds, self.log_stack)

    def log_stack(self, signal, frame):
        """Signal handler to log the stack trace of the current thread.

        For use with set_blocking_signal_threshold.
        """
        logging.warning('IOLoop blocked for %f seconds in\n%s',
                        self._blocking_signal_threshold,
                        ''.join(traceback.format_stack(frame)))

    def start(self):
        """Starts the I/O loop.

        The loop will run until one of the I/O handlers calls stop(), which
        will make the loop stop after the current event iteration completes.
        """
        if self._stopped:
            self._stopped = False
            return
        self._thread_ident = thread_get_ident()
        self._running = True
        while True:
            poll_timeout = 3600.0

            # Prevent IO event starvation by delaying new callbacks
            # to the next iteration of the event loop.
            with self._callback_lock:
                callbacks = self._callbacks
                self._callbacks = []
            for callback in callbacks:
                self._run_callback(callback)

            if self._timeouts:
                now = time.time()
                while self._timeouts:
                    if self._timeouts[0].callback is None:
                        # the timeout was cancelled
                        heapq.heappop(self._timeouts)
                    elif self._timeouts[0].deadline <= now:
                        timeout = heapq.heappop(self._timeouts)
                        self._run_callback(timeout.callback)
                    else:
                        seconds = self._timeouts[0].deadline - now
                        poll_timeout = min(seconds, poll_timeout)
                        break

            if self._callbacks:
                # If any callbacks or timeouts called add_callback,
                # we don't want to wait in poll() before we run them.
                poll_timeout = 0.0

            if not self._running:
                break

            if self._blocking_signal_threshold is not None:
                # clear alarm so it doesn't fire while poll is waiting for
                # events.
                signal.setitimer(signal.ITIMER_REAL, 0, 0)

            try:
                event_pairs = self._impl.poll(poll_timeout)
            except Exception as e:
                # Depending on python version and IOLoop implementation,
                # different exception types may be thrown and there are
                # two ways EINTR might be signaled:
                # * e.errno == errno.EINTR
                # * e.args is like (errno.EINTR, 'Interrupted system call')
                if (getattr(e, 'errno', None) == errno.EINTR or
                    (isinstance(getattr(e, 'args', None), tuple) and
                     len(e.args) == 2 and e.args[0] == errno.EINTR)):
                    continue
                elif getattr(e, 'errno', None) == ETERM:
                    # This happens when the zmq Context is closed; we should just exit.
                    self._running = False
                    self._stopped = True
                    break
                else:
                    raise

            if self._blocking_signal_threshold is not None:
                signal.setitimer(signal.ITIMER_REAL,
                                 self._blocking_signal_threshold, 0)

            # Pop one fd at a time from the set of pending fds and run
            # its handler. Since that handler may perform actions on
            # other file descriptors, there may be reentrant calls to
            # this IOLoop that update self._events
            self._events.update(event_pairs)
            while self._events:
                fd, events = self._events.popitem()
                try:
                    self._handlers[fd](fd, events)
                except (OSError, IOError) as e:
                    if e.args[0] == errno.EPIPE:
                        # Happens when the client closes the connection
                        pass
                    else:
                        logging.error("Exception in I/O handler for fd %s",
                                      fd, exc_info=True)
                except Exception:
                    logging.error("Exception in I/O handler for fd %s",
                                  fd, exc_info=True)
        # reset the stopped flag so another start/stop pair can be issued
        self._stopped = False
        if self._blocking_signal_threshold is not None:
            signal.setitimer(signal.ITIMER_REAL, 0, 0)

    def stop(self):
        """Stop the loop after the current event loop iteration is complete.
        If the event loop is not currently running, the next call to start()
        will return immediately.

        To use asynchronous methods from otherwise-synchronous code (such as
        unit tests), you can start and stop the event loop like this::

          ioloop = IOLoop()
          async_method(ioloop=ioloop, callback=ioloop.stop)
          ioloop.start()

        ioloop.start() will return after async_method has run its callback,
        whether that callback was invoked before or after ioloop.start.

        Note that even after `stop` has been called, the IOLoop is not
        completely stopped until `IOLoop.start` has also returned.
        """
        self._running = False
        self._stopped = True
        self._waker.wake()

    def running(self):
        """Returns true if this IOLoop is currently running."""
        return self._running

    def add_timeout(self, deadline, callback):
        """Calls the given callback at the time deadline from the I/O loop.

        Returns a handle that may be passed to remove_timeout to cancel.

        ``deadline`` may be a number denoting a unix timestamp (as returned
        by ``time.time()`` or a ``datetime.timedelta`` object for a deadline
        relative to the current time.

        Note that it is not safe to call `add_timeout` from other threads.
        Instead, you must use `add_callback` to transfer control to the
        IOLoop's thread, and then call `add_timeout` from there.
        """
        timeout = _Timeout(deadline, stack_context.wrap(callback))
        heapq.heappush(self._timeouts, timeout)
        return timeout

    def remove_timeout(self, timeout):
        """Cancels a pending timeout.

        The argument is a handle as returned by add_timeout.
        """
        # Removing from a heap is complicated, so just leave the defunct
        # timeout object in the queue (see discussion in
        # http://docs.python.org/library/heapq.html).
        # If this turns out to be a problem, we could add a garbage
        # collection pass whenever there are too many dead timeouts.
        timeout.callback = None

    def add_callback(self, callback):
        """Calls the given callback on the next I/O loop iteration.

        It is safe to call this method from any thread at any time.
        Note that this is the *only* method in IOLoop that makes this
        guarantee; all other interaction with the IOLoop must be done
        from that IOLoop's thread.  add_callback() may be used to transfer
        control from other threads to the IOLoop's thread.
        """
        with self._callback_lock:
            list_empty = not self._callbacks
            self._callbacks.append(stack_context.wrap(callback))
        if list_empty and thread_get_ident() != self._thread_ident:
            # If we're in the IOLoop's thread, we know it's not currently
            # polling.  If we're not, and we added the first callback to an
            # empty list, we may need to wake it up (it may wake up on its
            # own, but an occasional extra wake is harmless).  Waking
            # up a polling IOLoop is relatively expensive, so we try to
            # avoid it when we can.
            self._waker.wake()

    def _run_callback(self, callback):
        try:
            callback()
        except Exception:
            self.handle_callback_exception(callback)

    def handle_callback_exception(self, callback):
        """This method is called whenever a callback run by the IOLoop
        throws an exception.

        By default simply logs the exception as an error.  Subclasses
        may override this method to customize reporting of exceptions.

        The exception itself is not passed explicitly, but is available
        in sys.exc_info.
        """
        logging.error("Exception in callback %r", callback, exc_info=True)


class _Timeout(object):
    """An IOLoop timeout, a UNIX timestamp and a callback"""

    # Reduce memory overhead when there are lots of pending callbacks
    __slots__ = ['deadline', 'callback']

    def __init__(self, deadline, callback):
        if isinstance(deadline, (int, long, float)):
            self.deadline = deadline
        elif isinstance(deadline, datetime.timedelta):
            self.deadline = time.time() + _Timeout.timedelta_to_seconds(deadline)
        else:
            raise TypeError("Unsupported deadline %r" % deadline)
        self.callback = callback

    @staticmethod
    def timedelta_to_seconds(td):
        """Equivalent to td.total_seconds() (introduced in python 2.7)."""
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / float(10 ** 6)

    # Comparison methods to sort by deadline, with object id as a tiebreaker
    # to guarantee a consistent ordering.  The heapq module uses __le__
    # in python2.5, and __lt__ in 2.6+ (sort() and most other comparisons
    # use __lt__).
    def __lt__(self, other):
        return ((self.deadline, id(self)) <
                (other.deadline, id(other)))

    def __le__(self, other):
        return ((self.deadline, id(self)) <=
                (other.deadline, id(other)))


class PeriodicCallback(object):
    """Schedules the given callback to be called periodically.

    The callback is called every callback_time milliseconds.

    `start` must be called after the PeriodicCallback is created.
    """
    def __init__(self, callback, callback_time, io_loop=None):
        self.callback = callback
        self.callback_time = callback_time
        self.io_loop = io_loop or IOLoop.instance()
        self._running = False
        self._timeout = None

    def start(self):
        """Starts the timer."""
        self._running = True
        self._next_timeout = time.time()
        self._schedule_next()

    def stop(self):
        """Stops the timer."""
        self._running = False
        if self._timeout is not None:
            self.io_loop.remove_timeout(self._timeout)
            self._timeout = None

    def _run(self):
        if not self._running:
            return
        try:
            self.callback()
        except Exception:
            logging.error("Error in periodic callback", exc_info=True)
        self._schedule_next()

    def _schedule_next(self):
        if self._running:
            current_time = time.time()
            while self._next_timeout <= current_time:
                self._next_timeout += self.callback_time / 1000.0
            self._timeout = self.io_loop.add_timeout(self._next_timeout, self._run)

class DelayedCallback(PeriodicCallback):
    """Schedules the given callback to be called once.

    The callback is called once, after callback_time milliseconds.

    `start` must be called after the DelayedCallback is created.
    
    The timeout is calculated from when `start` is called.
    """
    
    def start(self):
        """Starts the timer."""
        self._running = True
        self._firstrun = True
        self._next_timeout = time.time() + self.callback_time / 1000.0
        self.io_loop.add_timeout(self._next_timeout, self._run)
    
    def _run(self):
        if not self._running: return
        self._running = False
        try:
            self.callback()
        except Exception:
            logging.error("Error in delayed callback", exc_info=True)


class ZMQPoller(object):
    """A poller that can be used in the tornado IOLoop.
    
    This simply wraps a regular zmq.Poller, scaling the timeout
    by 1000, so that it is in seconds rather than milliseconds.
    """
    
    def __init__(self):
        self._poller = Poller()
    
    @staticmethod
    def _map_events(events):
        """translate IOLoop.READ/WRITE/ERROR event masks into zmq.POLLIN/OUT/ERR"""
        z_events = 0
        if events & IOLoop.READ:
            z_events |= POLLIN
        if events & IOLoop.WRITE:
            z_events |= POLLOUT
        if events & IOLoop.ERROR:
            z_events |= POLLERR
        return z_events
    
    @staticmethod
    def _remap_events(z_events):
        """translate zmq.POLLIN/OUT/ERR event masks into IOLoop.READ/WRITE/ERROR"""
        events = 0
        if z_events & POLLIN:
            events |= IOLoop.READ
        if z_events & POLLOUT:
            events |= IOLoop.WRITE
        if z_events & POLLERR:
            events |= IOLoop.ERROR
        return events
    
    def register(self, fd, events):
        return self._poller.register(fd, self._map_events(events))
    
    def modify(self, fd, events):
        return self._poller.modify(fd, self._map_events(events))
    
    def unregister(self, fd):
        return self._poller.unregister(fd)
    
    def poll(self, timeout):
        """poll in seconds rather than milliseconds.
        
        Event masks will be IOLoop.READ/WRITE/ERROR
        """
        z_events = self._poller.poll(1000*timeout)
        return [ (fd,self._remap_events(evt)) for (fd,evt) in z_events ]
    
    def close(self):
        pass

_poll = ZMQPoller

def install():
    """set the tornado IOLoop instance with the pyzmq IOLoop.
    
    After calling this function, tornado's IOLoop.instance() and pyzmq's
    IOLoop.instance() will return the same object.
    
    An assertion error will be raised if tornado's IOLoop has been initialized
    prior to calling this function.
    """
    from tornado import ioloop
    # check if tornado's IOLoop is already initialized to something other
    # than the pyzmq IOLoop instance:
    assert (not ioloop.IOLoop.initialized()) or \
        ioloop.IOLoop.instance() is IOLoop.instance(), "tornado IOLoop already initialized"
    # register as instance with tornado.ioloop
    ioloop.IOLoop._instance = IOLoop.instance()

