"""0MQ polling related functions and classes."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import zmq
from .backend import zmq_poll
from .constants import POLLIN, POLLOUT, POLLERR

#-----------------------------------------------------------------------------
# Polling related methods
#-----------------------------------------------------------------------------


class Poller(object):
    """Poller()

    A stateful poll interface that mirrors Python's built-in poll.
    """

    def __init__(self):
        self.sockets = {}

    def register(self, socket, flags=POLLIN|POLLOUT):
        """p.register(socket, flags=POLLIN|POLLOUT)

        Register a 0MQ socket or native fd for I/O monitoring.
        
        register(s,0) is equivalent to unregister(s).

        Parameters
        ----------
        socket : zmq.Socket or native socket
            A zmq.Socket or any Python object having a ``fileno()`` 
            method that returns a valid file descriptor.
        flags : int
            The events to watch for.  Can be POLLIN, POLLOUT or POLLIN|POLLOUT.
            If `flags=0`, socket will be unregistered.
        """
        if flags:
            self.sockets[socket] = flags
        elif socket in self.sockets:
            # uregister sockets registered with no events
            self.unregister(socket)
        else:
            # ignore new sockets with no events
            pass

    def modify(self, socket, flags=POLLIN|POLLOUT):
        """p.modify(socket, flags=POLLIN|POLLOUT)

        Modify the flags for an already registered 0MQ socket or native fd.
        """
        self.register(socket, flags)

    def unregister(self, socket):
        """p.unregister(socket)

        Remove a 0MQ socket or native fd for I/O monitoring.

        Parameters
        ----------
        socket : Socket
            The socket instance to stop polling.
        """
        del self.sockets[socket]

    def poll(self, timeout=None):
        """p.poll(timeout=None)

        Poll the registered 0MQ or native fds for I/O.

        Parameters
        ----------
        timeout : float, int
            The timeout in milliseconds. If None, no `timeout` (infinite). This
            is in milliseconds to be compatible with ``select.poll()``. The
            underlying zmq_poll uses microseconds and we convert to that in
            this function.
        """
        if timeout is None:
            timeout = -1
        
        timeout = int(timeout)
        if timeout < 0:
            timeout = -1
        return zmq_poll(list(self.sockets.items()), timeout=timeout)


def select(rlist, wlist, xlist, timeout=None):
    """select(rlist, wlist, xlist, timeout=None) -> (rlist, wlist, xlist)

    Return the result of poll as a lists of sockets ready for r/w/exception.

    This has the same interface as Python's built-in ``select.select()`` function.

    Parameters
    ----------
    timeout : float, int, optional
        The timeout in seconds. If None, no timeout (infinite). This is in seconds to be
        compatible with ``select.select()``. The underlying zmq_poll uses microseconds
        and we convert to that in this function.
    rlist : list of sockets/FDs
        sockets/FDs to be polled for read events
    wlist : list of sockets/FDs
        sockets/FDs to be polled for write events
    xlist : list of sockets/FDs
        sockets/FDs to be polled for error events
    
    Returns
    -------
    (rlist, wlist, xlist) : tuple of lists of sockets (length 3)
        Lists correspond to sockets available for read/write/error events respectively.
    """
    if timeout is None:
        timeout = -1
    # Convert from sec -> us for zmq_poll.
    # zmq_poll accepts 3.x style timeout in ms
    timeout = int(timeout*1000.0)
    if timeout < 0:
        timeout = -1
    sockets = []
    for s in set(rlist + wlist + xlist):
        flags = 0
        if s in rlist:
            flags |= POLLIN
        if s in wlist:
            flags |= POLLOUT
        if s in xlist:
            flags |= POLLERR
        sockets.append((s, flags))
    return_sockets = zmq_poll(sockets, timeout)
    rlist, wlist, xlist = [], [], []
    for s, flags in return_sockets:
        if flags & POLLIN:
            rlist.append(s)
        if flags & POLLOUT:
            wlist.append(s)
        if flags & POLLERR:
            xlist.append(s)
    return rlist, wlist, xlist

#-----------------------------------------------------------------------------
# Symbols to export
#-----------------------------------------------------------------------------

__all__ = [ 'Poller', 'select' ]
