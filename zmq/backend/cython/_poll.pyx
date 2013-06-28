"""0MQ polling related functions and classes."""

#
#    Copyright (c) 2010-2011 Brian E. Granger & Min Ragan-Kelley
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from libc.stdlib cimport free, malloc

from libzmq cimport zmq_pollitem_t, ZMQ_VERSION_MAJOR
from libzmq cimport zmq_poll as zmq_poll_c
from socket cimport Socket

import sys

from zmq.backend.cython.checkrc cimport _check_rc

#-----------------------------------------------------------------------------
# Polling related methods
#-----------------------------------------------------------------------------

# version-independent typecheck for int/long
if sys.version_info[0] >= 3:
    int_t = int
else:
    int_t = (int,long)


def zmq_poll(sockets, long timeout=-1):
    """zmq_poll(sockets, timeout=-1)

    Poll a set of 0MQ sockets, native file descs. or sockets.

    Parameters
    ----------
    sockets : list of tuples of (socket, flags)
        Each element of this list is a two-tuple containing a socket
        and a flags. The socket may be a 0MQ socket or any object with
        a ``fileno()`` method. The flags can be zmq.POLLIN (for detecting
        for incoming messages), zmq.POLLOUT (for detecting that send is OK)
        or zmq.POLLIN|zmq.POLLOUT for detecting both.
    timeout : int
        The number of milliseconds to poll for. Negative means no timeout.
    """
    cdef int rc, i
    cdef zmq_pollitem_t *pollitems = NULL
    cdef int nsockets = <int>len(sockets)
    cdef Socket current_socket
    
    if nsockets == 0:
        return []
    
    pollitems = <zmq_pollitem_t *>malloc(nsockets*sizeof(zmq_pollitem_t))
    if pollitems == NULL:
        raise MemoryError("Could not allocate poll items")
        
    if ZMQ_VERSION_MAJOR < 3:
        # timeout is us in 2.x, ms in 3.x
        # expected input is ms (matches 3.x)
        timeout = 1000*timeout
    
    for i in range(nsockets):
        s, events = sockets[i]
        if isinstance(s, Socket):
            pollitems[i].socket = (<Socket>s).handle
            pollitems[i].events = events
            pollitems[i].revents = 0
        elif isinstance(s, int_t):
            pollitems[i].socket = NULL
            pollitems[i].fd = s
            pollitems[i].events = events
            pollitems[i].revents = 0
        elif hasattr(s, 'fileno'):
            try:
                fileno = int(s.fileno())
            except:
                free(pollitems)
                raise ValueError('fileno() must return a valid integer fd')
            else:
                pollitems[i].socket = NULL
                pollitems[i].fd = fileno
                pollitems[i].events = events
                pollitems[i].revents = 0
        else:
            free(pollitems)
            raise TypeError(
                "Socket must be a 0MQ socket, an integer fd or have "
                "a fileno() method: %r" % s
            )
    

    with nogil:
        rc = zmq_poll_c(pollitems, nsockets, timeout)
    
    if rc < 0:
        free(pollitems)
        _check_rc(rc)
    
    results = []
    for i in range(nsockets):
        revents = pollitems[i].revents
        # for compatibility with select.poll:
        # - only return sockets with non-zero status
        # - return the fd for plain sockets
        if revents > 0:
            if pollitems[i].socket != NULL:
                s = sockets[i][0]
            else:
                s = pollitems[i].fd
            results.append((s, revents))

    free(pollitems)
    return results

#-----------------------------------------------------------------------------
# Symbols to export
#-----------------------------------------------------------------------------

__all__ = [ 'zmq_poll' ]
