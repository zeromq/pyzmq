"""Python bindings for 0MQ."""

#
#    Copyright (c) 2010 Brian E. Granger
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


from stdlib cimport *
from python_string cimport PyString_FromStringAndSize
from python_string cimport PyString_AsStringAndSize
from python_string cimport PyString_AsString, PyString_Size

cdef extern from "Python.h":
    ctypedef int Py_ssize_t

import cPickle as pickle
import random

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        json = None

include "allocate.pxi"

#-----------------------------------------------------------------------------
# Import the C header files
#-----------------------------------------------------------------------------

cdef extern from "errno.h" nogil:
    enum: EINVAL
    enum: EAGAIN

cdef extern from "string.h" nogil:
    void *memcpy(void *dest, void *src, size_t n)
    size_t strlen(char *s)

cdef extern from "zmq.h" nogil:
    ctypedef int int64_t
    enum: ZMQ_HAUSNUMERO
    enum: ENOTSUP
    enum: EPROTONOSUPPORT
    enum: ENOBUFS
    enum: ENETDOWN
    enum: EADDRINUSE
    enum: EADDRNOTAVAIL
    enum: ECONNREFUSED
    enum: EINPROGRESS
    enum: EMTHREAD
    enum: EFSM
    enum: ENOCOMPATPROTO

    enum: errno
    char *zmq_strerror (int errnum)
    int zmq_errno()

    enum: ZMQ_MAX_VSM_SIZE # 30
    enum: ZMQ_DELIMITER # 31
    enum: ZMQ_VSM # 32

    ctypedef struct zmq_msg_t:
        void *content
        unsigned char shared
        unsigned char vsm_size
        unsigned char vsm_data [ZMQ_MAX_VSM_SIZE]
    
    ctypedef void zmq_free_fn(void *data, void *hint)
    
    int zmq_msg_init (zmq_msg_t *msg)
    int zmq_msg_init_size (zmq_msg_t *msg, size_t size)
    int zmq_msg_init_data (zmq_msg_t *msg, void *data,
        size_t size, zmq_free_fn *ffn, void *hint)
    int zmq_msg_close (zmq_msg_t *msg)
    int zmq_msg_move (zmq_msg_t *dest, zmq_msg_t *src)
    int zmq_msg_copy (zmq_msg_t *dest, zmq_msg_t *src)
    void *zmq_msg_data (zmq_msg_t *msg)
    size_t zmq_msg_size (zmq_msg_t *msg)
    
    enum: ZMQ_POLL # 1

    void *zmq_init (int app_threads, int io_threads, int flags)
    int zmq_term (void *context)

    enum: ZMQ_P2P # 0
    enum: ZMQ_PUB # 1
    enum: ZMQ_SUB # 2
    enum: ZMQ_REQ # 3
    enum: ZMQ_REP # 4
    enum: ZMQ_XREQ # 5
    enum: ZMQ_XREP # 6
    enum: ZMQ_UPSTREAM # 7
    enum: ZMQ_DOWNSTREAM # 8

    enum: ZMQ_HWM # 1
    enum: ZMQ_LWM # 2
    enum: ZMQ_SWAP # 3
    enum: ZMQ_AFFINITY # 4
    enum: ZMQ_IDENTITY # 5
    enum: ZMQ_SUBSCRIBE # 6
    enum: ZMQ_UNSUBSCRIBE # 7
    enum: ZMQ_RATE # 8
    enum: ZMQ_RECOVERY_IVL # 9
    enum: ZMQ_MCAST_LOOP # 10
    enum: ZMQ_SNDBUF # 11
    enum: ZMQ_RCVBUF # 12

    enum: ZMQ_NOBLOCK # 1

    void *zmq_socket (void *context, int type)
    int zmq_close (void *s)
    int zmq_setsockopt (void *s, int option, void *optval, size_t optvallen)
    int zmq_bind (void *s, char *addr)
    int zmq_connect (void *s, char *addr)
    int zmq_send (void *s, zmq_msg_t *msg, int flags)
    int zmq_recv (void *s, zmq_msg_t *msg, int flags)
    
    enum: ZMQ_POLLIN # 1
    enum: ZMQ_POLLOUT # 2
    enum: ZMQ_POLLERR # 4

    ctypedef struct zmq_pollitem_t:
        void *socket
        int fd
        # #if defined _WIN32
        #     SOCKET fd;
        short events
        short revents

    int zmq_poll (zmq_pollitem_t *items, int nitems, long timeout)

    void *zmq_stopwatch_start ()
    unsigned long zmq_stopwatch_stop (void *watch_)
    void zmq_sleep (int seconds_)

#-----------------------------------------------------------------------------
# Python module level constants
#-----------------------------------------------------------------------------

NOBLOCK = ZMQ_NOBLOCK
P2P = ZMQ_P2P
PUB = ZMQ_PUB
SUB = ZMQ_SUB
REQ = ZMQ_REQ
REP = ZMQ_REP
XREQ = ZMQ_XREQ
XREP = ZMQ_XREP
UPSTREAM = ZMQ_UPSTREAM
DOWNSTREAM = ZMQ_DOWNSTREAM
HWM = ZMQ_HWM
LWM = ZMQ_LWM
SWAP = ZMQ_SWAP
AFFINITY = ZMQ_AFFINITY
IDENTITY = ZMQ_IDENTITY
SUBSCRIBE = ZMQ_SUBSCRIBE
UNSUBSCRIBE = ZMQ_UNSUBSCRIBE
RATE = ZMQ_RATE
RECOVERY_IVL = ZMQ_RECOVERY_IVL
MCAST_LOOP = ZMQ_MCAST_LOOP
SNDBUF = ZMQ_SNDBUF
RCVBUF = ZMQ_RCVBUF
POLL = ZMQ_POLL
POLLIN = ZMQ_POLLIN
POLLOUT = ZMQ_POLLOUT
POLLERR = ZMQ_POLLERR

#-----------------------------------------------------------------------------
# Error handling
#-----------------------------------------------------------------------------

def strerror(errnum):
    """Return the error string given the error number."""
    return zmq_strerror(errnum)

class ZMQError(Exception):
    """Base exception class for 0MQ errors in Python."""
    pass

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

cdef class Context:
    """Manage the lifecycle of a 0MQ context.

    Context(app_threads=1, io_threads=1, flags=0)

    Parameters
    ----------
    app_threads : int
        The number of application threads.
    io_threads : int
        The number of IO threads.
    flags : int
        Any of the Context flags.  Use zmq.POLL to put all sockets into
        non blocking mode and use poll.
    """

    cdef void *handle

    def __cinit__(self, int app_threads=1, int io_threads=1, int flags=0):
        self.handle = NULL
        self.handle = zmq_init(app_threads, io_threads, flags)
        if self.handle == NULL:
            raise ZMQError(zmq_strerror(zmq_errno()))

    def __dealloc__(self):
        cdef int rc
        if self.handle != NULL:
            rc = zmq_term(self.handle)
            if rc != 0:
                raise ZMQError(zmq_strerror(zmq_errno()))

    def socket(self, int socket_type):
        """Create a Socket associated with this Context.

        Parameters
        ----------
        socket_type : int
            The socket type, which can be any of the 0MQ socket types: 
            REQ, REP, PUB, SUB, P2P, XREQ, XREP, UPSTREAM, DOWNSTREAM.
        """
        return Socket(self, socket_type)


cdef class Socket:
    """A 0MQ socket.

    Socket(context, socket_type)

    Parameters
    ----------
    context : Context
        The 0MQ Context this Socket belongs to.
    socket_type : int
        The socket type, which can be any of the 0MQ socket types: 
        REQ, REP, PUB, SUB, P2P, XREQ, XREP, UPSTREAM, DOWNSTREAM.
    """

    cdef void *handle
    cdef public int socket_type
    # Hold on to a reference to the context to make sure it is not garbage
    # collected until the socket it done with it.
    cdef public Context context
    cdef public object closed

    def __cinit__(self, Context context, int socket_type):
        self.handle = NULL
        self.context = context
        self.socket_type = socket_type
        self.handle = zmq_socket(context.handle, socket_type)
        if self.handle == NULL:
            raise ZMQError(zmq_strerror(zmq_errno()))
        self.closed = False

    def __dealloc__(self):
        self.close()

    def close(self):
        """Close the socket.

        This can be called to close the socket by hand. If this is not
        called, the socket will automatically be closed when it is
        garbage collected.
        """
        cdef int rc
        if self.handle != NULL and not self.closed:
            rc = zmq_close(self.handle)
            if rc != 0:
                raise ZMQError(zmq_strerror(zmq_errno()))
            self.handle = NULL
            self.closed = True

    def _check_closed(self):
        if self.closed:
            raise ZMQError("Cannot complete operation, Socket is closed.")

    def setsockopt(self, option, optval):
        """Set socket options.

        See the 0MQ documentation for details on specific options.

        Parameters
        ----------
        option : str
            The name of the option to set. Can be any of: SUBSCRIBE, 
            UNSUBSCRIBE, IDENTITY, HWM, LWM, SWAP, AFFINITY, RATE, 
            RECOVERY_IVL, MCAST_LOOP, SNDBUF, RCVBUF.
        optval : int or str
            The value of the option to set.
"""
        cdef int64_t optval_int_c
        cdef int rc

        self._check_closed()

        if not isinstance(option, int):
            raise TypeError('expected int, got: %r' % option)

        if option in [SUBSCRIBE, UNSUBSCRIBE, IDENTITY]:
            if not isinstance(optval, str):
                raise TypeError('expected str, got: %r' % optval)
            opt_val_str_c = optval
            rc = zmq_setsockopt(
                self.handle, option,
                PyString_AsString(optval), PyString_Size(optval)
            )
        elif option in [HWM, LWM, SWAP, AFFINITY, RATE, RECOVERY_IVL,
                        MCAST_LOOP, SNDBUF, RCVBUF]:
            if not isinstance(optval, int):
                raise TypeError('expected int, got: %r' % optval)
            optval_int_c = optval
            rc = zmq_setsockopt(
                self.handle, option,
                &optval_int_c, sizeof(int64_t)
            )
        else:
            raise ZMQError(zmq_strerror(EINVAL))

        if rc != 0:
            raise ZMQError(zmq_strerror(zmq_errno()))

    def bind(self, addr):
        """Bind the socket to an address.

        This causes the socket to listen on a network port. Sockets on the
        other side of this connection will use :meth:`Sockiet.connect` to
        connect to this socket.

        Parameters
        ----------
        addr : str
            The address string. This has the form 'protocol://interface:port',
            for example 'tcp://127.0.0.1:555'. Protocols supported are
            tcp, upd, pgm, iproc and ipc.
        """
        cdef int rc

        self._check_closed()

        if not isinstance(addr, str):
            raise TypeError('expected str, got: %r' % addr)
        rc = zmq_bind(self.handle, addr)
        if rc != 0:
            raise ZMQError(zmq_strerror(zmq_errno()))

    def bind_to_random_port(self, addr, min_port=2000, max_port=20000, max_tries=100):
        """Bind this socket to a random port in a range.

        Parameters
        ----------
        addr : str
            The address string without the port to pass to :meth:`Socket.bind`.
        min_port : int
            The minimum port in the range of ports to try.
        max_port : int
            The maximum port in the range of ports to try.
        max_tries : int
            The number of attempt to bind.

        Returns
        -------
        port : int
            The port the socket was bound to.
        """
        for i in range(max_tries):
            try:
                port = random.randrange(min_port, max_port)
                self.bind('%s:%s' % (addr, port))
            except ZMQError:
                pass
            else:
                return port
        raise ZMQError("Could not bind socket to random port.")
        

    def connect(self, addr):
        """Connect to a remote 0MQ socket.

        Parameters
        ----------
        addr : str
            The address string. This has the form 'protocol://interface:port',
            for example 'tcp://127.0.0.1:555'. Protocols supported are
            tcp, upd, pgm, iproc and ipc.
        """
        cdef int rc

        self._check_closed()

        if not isinstance(addr, str):
            raise TypeError('expected str, got: %r' % addr)
        rc = zmq_connect(self.handle, addr)
        if rc != 0:
            raise ZMQError(zmq_strerror(zmq_errno()))

    def send(self, msg, int flags=0):
        """Send a message.

        This queues the message to be sent by the IO thread at a later time.

        Parameters
        ----------
        flags : int
            Any supported flag: NOBLOCK.

        Returns
        -------
        result : bool
            True if message was send, False if message was not sent (EAGAIN).
        """
        cdef int rc, rc2
        cdef zmq_msg_t data
        cdef char *msg_c
        cdef Py_ssize_t msg_c_len

        self._check_closed()

        if not isinstance(msg, str):
            raise TypeError('expected str, got: %r' % msg)

        # If zmq_msg_init_* fails do we need to call zmq_msg_close?

        PyString_AsStringAndSize(msg, &msg_c, &msg_c_len)
        # Copy the msg before sending. This avoids any complications with
        # the GIL, etc.
        rc = zmq_msg_init_size(&data, msg_c_len)
        memcpy(zmq_msg_data(&data), msg_c, zmq_msg_size(&data))

        if rc != 0:
            raise ZMQError(zmq_strerror(zmq_errno()))

        with nogil:
            rc = zmq_send(self.handle, &data, flags)
        rc2 = zmq_msg_close(&data)

        # Shouldn't the error handling for zmq_msg_close come after that
        # of zmq_send?
        if rc2 != 0:
            raise ZMQError(zmq_strerror(zmq_errno()))

        if rc != 0:
            if zmq_errno() == EAGAIN:
                return False
            else:
                raise ZMQError(zmq_strerror(zmq_errno()))
        else:
            return True

    def recv(self, int flags=0):
        """Receive a message.

        Parameters
        ----------
        flags : int
            Any supported flag: NOBLOCK. If NOBLOCK is set, this method
            will return None if a message is not ready. If NOBLOCK is not
            set, then this method will block until a message arrives.

        Returns
        -------
        msg : str
            The returned message or None of NOBLOCK is set and no message
            has arrived.
        """
        cdef int rc
        cdef zmq_msg_t data

        self._check_closed()

        rc = zmq_msg_init(&data)
        if rc != 0:
            raise ZMQError(zmq_strerror(zmq_errno()))

        with nogil:
            rc = zmq_recv(self.handle, &data, flags)

        if rc != 0:
            if zmq_errno() == EAGAIN:
                return None
            else:
                raise ZMQError(zmq_strerror(zmq_errno()))

        try:
            msg = PyString_FromStringAndSize(
                <char *>zmq_msg_data(&data), 
                zmq_msg_size(&data)
            )
        finally:
            rc = zmq_msg_close(&data)

        if rc != 0:
            raise ZMQError(zmq_strerror(zmq_errno()))
        return msg

    def send_pyobj(self, obj, flags=0, protocol=-1):
        """Send a Python object as a message using pickle to serialize.

        Parameters
        ----------
        obj : Python object
            The Python object to send.
        flags : int
            Any valid send flag.
        protocol : int
            The pickle protocol number to use. Default of -1 will select
            the highest supported number. Use 0 for multiple platform
            support.
        """
        msg = pickle.dumps(obj, protocol)
        return self.send(msg, flags)

    def recv_pyobj(self, flags=0):
        """Receive a Python object as a message using pickle to serialize.

        Parameters
        ----------
        flags : int
            Any valid recv flag.

        Returns
        -------
        obj : Python object
            The Python object that arrives as a message.
        """
        s = self.recv(flags)
        if s is not None:
            return pickle.loads(s)

    def send_json(self, obj, flags=0):
        """Send a Python object as a message using json to serialize.

        Parameters
        ----------
        obj : Python object
            The Python object to send.
        flags : int
            Any valid send flag.
        """
        if json is None:
            raise ImportError('json or simplejson library is required.')
        else:
            msg = json.dumps(obj, separators=(',',':'))
            return self.send(msg, flags)

    def recv_json(self, flags=0):
        """Receive a Python object as a message using json to serialize.

        Parameters
        ----------
        flags : int
            Any valid recv flag.

        Returns
        -------
        obj : Python object
            The Python object that arrives as a message.
        """
        if json is None:
            raise ImportError('json or simplejson library is required.')
        else:
            s = self.recv(flags)
            if s is not None:
                return json.loads(s)


cdef class Stopwatch:
    """A simple stopwatch based on zmq_stopwatch_start/stop."""

    cdef void *watch

    def __cinit__(self):
        self.watch = NULL

    def start(self):
        if self.watch == NULL:
            self.watch = zmq_stopwatch_start()
        else:
            raise ZMQError('Stopwatch is already runing.')

    def stop(self):
        if self.watch == NULL:
            raise ZMQError('Must start the Stopwatch before calling stop.')
        else:
            time = zmq_stopwatch_stop(self.watch)
            self.watch = NULL
            return time

    def clear(self):
        self.watch = NULL

    def sleep(self, int seconds):
        zmq_sleep(seconds)


def _poll(sockets, long timeout=-1):
    """Poll a set of 0MQ sockets, native file descs. or sockets.

    Parameters
    ----------
    sockets : list of tuples of (socket, flags)
        Each element of this list is a two-tuple containing a socket
        and a flags. The socket may be a 0MQ socket or any object with
        a :meth:`fileno` method. The flags can be zmq.POLLIN (for detecting
        for incoming messages), zmq.POLLOUT (for detecting that send is OK)
        or zmq.POLLIN|zmq.POLLOUT for detecting both.
    timeout : int
        The number of microseconds to poll for. Negative means no timeout.
    """
    cdef int rc, i
    cdef zmq_pollitem_t *pollitems = NULL
    cdef int nsockets = len(sockets)
    cdef Socket current_socket
    pollitems_o = allocate(nsockets*sizeof(zmq_pollitem_t),<void**>&pollitems)

    for i in range(nsockets):
        s = sockets[i][0]
        events = sockets[i][1]
        if isinstance(s, Socket):
            current_socket = s
            pollitems[i].socket = current_socket.handle
            pollitems[i].events = events
            pollitems[i].revents = 0
        elif isinstance(s, int):
            pollitems[i].socket = NULL
            pollitems[i].fd = s
            pollitems[i].events = events
            pollitems[i].revents = 0
        elif hasattr(s, 'fileno'):
            try:
                fileno = int(s.fileno())
            except:
                raise ValueError('fileno() must return an valid integer fd')
            else:
                pollitems[i].socket = NULL
                pollitems[i].fd = fileno
                pollitems[i].events = events
                pollitems[i].revents = 0
        else:
            raise TypeError(
                "Socket must be a 0MQ socket, an integer fd or have "
                "a fileno() method: %r" % s
            )

    # int zmq_poll (zmq_pollitem_t *items, int nitems, long timeout)
    with nogil:
        rc = zmq_poll(pollitems, nsockets, timeout)
    if rc == -1:
        raise ZMQError(zmq_strerror(zmq_errno()))
    
    results = []
    for i in range(nsockets):
        s = sockets[i][0]
        # Return the fd for sockets, for compat. with select.poll.
        if hasattr(s, 'fileno'):
            s = s.fileno()
        revents = pollitems[i].revents
        # Only return sockets with non-zero status for compat. with select.poll.
        if revents > 0:
            results.append((s, revents))

    return results


class Poller(object):
    """An stateful poll interface that mirrors Python's built-in poll."""

    def __init__(self):
        self.sockets = {}

    def register(self, socket, flags=POLLIN|POLLOUT):
        """Register a 0MQ socket or native fd for I/O monitoring.

        Parameters
        ----------
        socket : zmq.Socket or native socket
            A zmq.Socket or any Python object having a :meth:`fileno` 
            method that returns a valid file descriptor.
        flags : int
            The events to watch for.  Can be POLLIN, POLLOUT or POLLIN|POLLOUT.
        """
        self.sockets[socket] = flags

    def modify(self, socket, flags=POLLIN|POLLOUT):
        """Modify the flags for an already registered 0MQ socket or native fd."""
        self.register(socket, flags)

    def unregister(self, socket):
        """Remove a 0MQ socket or native fd for I/O monitoring.

        Parameters
        ----------
        socket : Socket
            The socket instance to stop polling.
        """
        del self.sockets[socket]

    def poll(self, timeout=None):
        """Poll the registered 0MQ or native fds for I/O.

        Parameters
        ----------
        timeout : int
            The timeout in microseconds. If None, no timeout (infinite).
        """
        if timeout is None:
            timeout = -1
        return _poll(self.sockets.items(), timeout=timeout)


def select(rlist, wlist, xlist, timeout=None):
    """Return the result of poll as a lists of sockets ready for r/w.

    This has the same interface as Python's built-in :func:`select` function.
    """
    if timeout is None:
        timeout = -1
    sockets = []
    for s in set(rlist+wlist+xlist):
        flags = 0
        if s in rlist:
            flags |= POLLIN
        if s in wlist:
            flags |= POLLOUT
        if s in xlist:
            flags |= POLLERR
        sockets.append(s)
    return_sockets = _poll(sockets, timeout)
    return_rlist = []
    return_wlist = []
    return_xlist = []
    for s,flags in return_sockets:
        if flags &POLLIN:
            return_rlist.append(s)
        if flags & POLLOUT:
            return_wlist.append(s)
        if flags & POLLERR:
            return_xlist.append(s)
    return return_rlist, return_wlist, return_xlist
    


__all__ = [
    'Context',
    'Socket',
    'ZMQError',
    'Stopwatch',
    'NOBLOCK',
    'P2P',
    'PUB',
    'SUB',
    'REQ',
    'REP',
    'XREQ',
    'XREP',
    'UPSTREAM',
    'DOWNSTREAM',
    'HWM',
    'LWM',
    'SWAP',
    'AFFINITY',
    'IDENTITY',
    'SUBSCRIBE',
    'UNSUBSCRIBE',
    'RATE',
    'RECOVERY_IVL',
    'MCAST_LOOP',
    'SNDBUF',
    'RCVBUF',
    'POLL',
    'POLLIN',
    'POLLOUT',
    'POLLERR',
    '_poll',
    'select',
    'Poller'
]

