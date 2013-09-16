# coding: utf-8
"""tornado IOLoop API with zmq compatibility

If you have tornado ≥ 3.0, this is a subclass of tornado's IOLoop,
otherwise we ship a minimal subset of tornado in zmq.eventloop.minitornado.

The minimal shipped version of tornado's IOLoop does not include
support for concurrent futures - this will only be available if you
have tornado ≥ 3.0.

Authors
-------
* MinRK
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from __future__ import absolute_import, division, with_statement

import os
import time
import warnings

from zmq import (
    Poller,
    POLLIN, POLLOUT, POLLERR,
    ZMQError, ETERM,
)

try:
    import tornado
    tornado_version = tornado.version_info
except (ImportError, AttributeError):
    tornado_version = ()

try:
    # tornado ≥ 3
    from tornado.ioloop import PollIOLoop, PeriodicCallback
    from tornado.log import gen_log
except ImportError:
    from .minitornado.ioloop import PollIOLoop, PeriodicCallback
    from .minitornado.log import gen_log


class DelayedCallback(PeriodicCallback):
    """Schedules the given callback to be called once.

    The callback is called once, after callback_time milliseconds.

    `start` must be called after the DelayedCallback is created.
    
    The timeout is calculated from when `start` is called.
    """
    def __init__(self, callback, callback_time, io_loop=None):
        # PeriodicCallback require callback_time to be positive
        warnings.warn("""DelayedCallback is deprecated.
        Use loop.add_timeout instead.""", DeprecationWarning)
        callback_time = max(callback_time, 1e-3)
        super(DelayedCallback, self).__init__(callback, callback_time, io_loop)
    
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
            gen_log.error("Error in delayed callback", exc_info=True)


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


class ZMQIOLoop(PollIOLoop):
    """ZMQ subclass of tornado's IOLoop"""
    def initialize(self, **kwargs):
        super(ZMQIOLoop, self).initialize(impl=ZMQPoller(), **kwargs)
    
    @staticmethod
    def instance():
        """Returns a global `IOLoop` instance.
        
        Most applications have a single, global `IOLoop` running on the
        main thread.  Use this method to get this instance from
        another thread.  To get the current thread's `IOLoop`, use `current()`.
        """
        # install ZMQIOLoop as the active IOLoop implementation
        # when using tornado 3
        if tornado_version >= (3,):
            PollIOLoop.configure(ZMQIOLoop)
        return PollIOLoop.instance()
    
    def start(self):
        try:
            super(ZMQIOLoop, self).start()
        except ZMQError as e:
            if e.errno == ETERM:
                # quietly return on ETERM
                pass
            else:
                raise e


if tornado_version >= (3,0) and tornado_version < (3,1):
    def backport_close(self, all_fds=False):
        """backport IOLoop.close to 3.0 from 3.1 (supports fd.close() method)"""
        from zmq.eventloop.minitornado.ioloop import PollIOLoop as mini_loop
        return mini_loop.close.__get__(self)(all_fds)
    ZMQIOLoop.close = backport_close


# public API name
IOLoop = ZMQIOLoop


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
    
    if tornado_version >= (3,):
        # tornado 3 has an official API for registering new defaults, yay!
        ioloop.IOLoop.configure(ZMQIOLoop)
    else:
        # we have to set the global instance explicitly
        ioloop.IOLoop._instance = IOLoop.instance()

