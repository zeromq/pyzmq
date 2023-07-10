"""Cython backend for pyzmq"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

try:
    import cython as C

    if not C.compiled:
        raise ImportError()
except ImportError:
    raise ImportError("zmq Cython backend has not been compiled") from None

from threading import Event
from weakref import ref

from cython import (
    NULL,
    Py_ssize_t,
    address,
    cast,
    cclass,
    char,
    declare,
    nogil,
    p_char,
    p_void,
    pointer,
    size_t,
    sizeof,
)
from cython.cimports.cpython import PyBytes_FromStringAndSize, PyErr_CheckSignals
from cython.cimports.libc.errno import EAGAIN, EINTR

# cimports require Cython 3
from cython.cimports.libc.stdint import uint32_t
from cython.cimports.libc.stdio import fprintf
from cython.cimports.libc.stdio import stderr as cstderr
from cython.cimports.libc.stdlib import free, malloc
from cython.cimports.libc.string import memcpy
from cython.cimports.zmq.backend.cython._externs import (
    getpid,
    mutex_allocate,
    mutex_lock,
    mutex_t,
    mutex_unlock,
)
from cython.cimports.zmq.backend.cython.libzmq import (
    ZMQ_ENOTSOCK,
    ZMQ_ETERM,
    ZMQ_IO_THREADS,
    ZMQ_VERSION_MAJOR,
    _zmq_version,
    zmq_ctx_destroy,
    zmq_ctx_get,
    zmq_ctx_new,
    zmq_ctx_set,
    zmq_curve_keypair,
    zmq_curve_public,
)
from cython.cimports.zmq.backend.cython.libzmq import zmq_errno as _zmq_errno
from cython.cimports.zmq.backend.cython.libzmq import (
    zmq_free_fn,
    zmq_has,
    zmq_init,
    zmq_msg_close,
    zmq_msg_copy,
    zmq_msg_data,
    zmq_msg_get,
    zmq_msg_gets,
    zmq_msg_group,
    zmq_msg_init,
    zmq_msg_init_data,
    zmq_msg_init_size,
    zmq_msg_routing_id,
    zmq_msg_send,
    zmq_msg_set,
    zmq_msg_set_group,
    zmq_msg_set_routing_id,
    zmq_msg_size,
    zmq_msg_t,
    zmq_strerror,
)
from cython.cimports.zmq.utils.buffers import asbuffer_r

import zmq
from zmq.error import InterruptedSystemCall, ZMQError, _check_version

# Python imports


@C.cfunc
@C.inline
@C.exceptval(-1)
def _check_rc(rc: C.int, error_without_errno: bool = False) -> C.int:
    """internal utility for checking zmq return condition

    and raising the appropriate Exception class
    """
    errno: C.int = _zmq_errno()
    PyErr_CheckSignals()
    if errno == 0 and not error_without_errno:
        return 0
    if rc == -1:  # if rc < -1, it's a bug in libzmq. Should we warn?
        if errno == EINTR:
            from zmq.error import InterruptedSystemCall

            raise InterruptedSystemCall(errno)
        elif errno == EAGAIN:
            from zmq.error import Again

            raise Again(errno)
        elif errno == ZMQ_ETERM:
            from zmq.error import ContextTerminated

            raise ContextTerminated(errno)
        else:
            from zmq.error import ZMQError

            raise ZMQError(errno)
    return 0


# message Frame class

_zhint = C.struct(
    sock=p_void,
    mutex=pointer(mutex_t),
    id=size_t,
)


@C.cfunc
@C.nogil
def free_python_msg(data: p_void, vhint: p_void) -> C.int:
    """A pure-C function for DECREF'ing Python-owned message data.

    Sends a message on a PUSH socket

    The hint is a `zhint` struct with two values:

    sock (void *): pointer to the Garbage Collector's PUSH socket
    id (size_t): the id to be used to construct a zmq_msg_t that should be sent on a PUSH socket,
       signaling the Garbage Collector to remove its reference to the object.

    When the Garbage Collector's PULL socket receives the message,
    it deletes its reference to the object,
    allowing Python to free the memory.
    """
    msg = declare(zmq_msg_t)
    msg_ptr: pointer(zmq_msg_t) = address(msg)
    hint: pointer(_zhint) = cast(pointer(_zhint), vhint)
    rc: C.int

    if hint != NULL:
        zmq_msg_init_size(msg_ptr, sizeof(size_t))
        memcpy(zmq_msg_data(msg_ptr), address(hint.id), sizeof(size_t))
        rc = mutex_lock(hint.mutex)
        if rc != 0:
            fprintf(cstderr, "pyzmq-gc mutex lock failed rc=%d\n", rc)
        rc = zmq_msg_send(msg_ptr, hint.sock, 0)
        if rc < 0:
            # gc socket could have been closed, e.g. during process teardown.
            # If so, ignore the failure because there's nothing to do.
            if _zmq_errno() != ZMQ_ENOTSOCK:
                fprintf(
                    cstderr, "pyzmq-gc send failed: %s\n", zmq_strerror(_zmq_errno())
                )
        rc = mutex_unlock(hint.mutex)
        if rc != 0:
            fprintf(cstderr, "pyzmq-gc mutex unlock failed rc=%d\n", rc)

        zmq_msg_close(msg_ptr)
        free(hint)
        return 0


@C.cfunc
@C.inline
def _copy_zmq_msg_bytes(zmq_msg: pointer(zmq_msg_t)) -> bytes:
    """Copy the data from a zmq_msg_t"""
    data_c: p_char = NULL
    data_len_c: Py_ssize_t
    data_c = cast(p_char, zmq_msg_data(zmq_msg))
    data_len_c = zmq_msg_size(zmq_msg)
    return PyBytes_FromStringAndSize(data_c, data_len_c)


_gc = None


@cclass
class Frame:
    def __init__(
        self, data=None, track=False, copy=None, copy_threshold=None, **kwargs
    ):
        rc: C.int
        data_c: p_char = NULL
        data_len_c: Py_ssize_t = 0
        hint: pointer(_zhint)
        if copy_threshold is None:
            copy_threshold = zmq.COPY_THRESHOLD

        zmq_msg_ptr: pointer(zmq_msg_t) = address(self.zmq_msg)
        # init more as False
        self.more = False

        # Save the data object in case the user wants the the data as a str.
        self._data = data
        self._failed_init = True  # bool switch for dealloc
        self._buffer = None  # buffer view of data
        self._bytes = None  # bytes copy of data

        self.tracker_event = None
        self.tracker = None
        # self.tracker should start finished
        # except in the case where we are sharing memory with libzmq
        if track:
            self.tracker = zmq._FINISHED_TRACKER

        if isinstance(data, str):
            raise TypeError("Str objects not allowed. Only: bytes, buffer interfaces.")

        if data is None:
            rc = zmq_msg_init(zmq_msg_ptr)
            _check_rc(rc)
            self._failed_init = False
            return

        asbuffer_r(data, cast(pointer(p_void), address(data_c)), address(data_len_c))

        # copy unspecified, apply copy_threshold
        if copy is None:
            if copy_threshold and data_len_c < copy_threshold:
                copy = True
            else:
                copy = False

        if copy:
            # copy message data instead of sharing memory
            rc = zmq_msg_init_size(zmq_msg_ptr, data_len_c)
            _check_rc(rc)
            memcpy(zmq_msg_data(zmq_msg_ptr), data_c, data_len_c)
            self._failed_init = False
            return

        # Getting here means that we are doing a true zero-copy Frame,
        # where libzmq and Python are sharing memory.
        # Hook up garbage collection with MessageTracker and zmq_free_fn

        # Event and MessageTracker for monitoring when zmq is done with data:
        if track:
            evt = Event()
            self.tracker_event = evt
            self.tracker = zmq.MessageTracker(evt)
        # create the hint for zmq_free_fn
        # two pointers: the gc context and a message to be sent to the gc PULL socket
        # allows libzmq to signal to Python when it is done with Python-owned memory.
        global _gc
        if _gc is None:
            from zmq.utils.garbage import gc as _gc

        hint: pointer(_zhint) = cast(pointer(_zhint), malloc(sizeof(_zhint)))
        hint.id = _gc.store(data, self.tracker_event)
        if not _gc._push_mutex:
            hint.mutex = mutex_allocate()
            _gc._push_mutex = cast(size_t, hint.mutex)
        else:
            hint.mutex = cast(pointer(mutex_t), cast(size_t, _gc._push_mutex))
        hint.sock = cast(p_void, cast(size_t, _gc._push_socket.underlying))

        rc = zmq_msg_init_data(
            zmq_msg_ptr,
            cast(p_void, data_c),
            data_len_c,
            cast(pointer(zmq_free_fn), free_python_msg),
            cast(p_void, hint),
        )
        if rc != 0:
            free(hint)
            _check_rc(rc)
        self._failed_init = False

    def __del__(self):
        if self._failed_init:
            return
        # This simply decreases the 0MQ ref-count of zmq_msg.
        with nogil:
            rc: C.int = zmq_msg_close(address(self.zmq_msg))
        _check_rc(rc)

    def __copy__(self):
        return self.fast_copy()

    def fast_copy(self) -> "Frame":
        new_msg: Frame = Frame()
        # This does not copy the contents, but just increases the ref-count
        # of the zmq_msg by one.
        zmq_msg_copy(address(new_msg.zmq_msg), address(self.zmq_msg))
        # Copy the ref to data so the copy won't create a copy when str is
        # called.
        if self._data is not None:
            new_msg._data = self._data
        if self._buffer is not None:
            new_msg._buffer = self._buffer
        if self._bytes is not None:
            new_msg._bytes = self._bytes

        # Frame copies share the tracker and tracker_event
        new_msg.tracker_event = self.tracker_event
        new_msg.tracker = self.tracker

        return new_msg

    # buffer interface code adapted from petsc4py by Lisandro Dalcin, a BSD project

    def __getbuffer__(self, buffer: pointer(Py_buffer), flags: C.int):  # noqa: F821
        # new-style (memoryview) buffer interface
        buffer.buf = zmq_msg_data(address(self.zmq_msg))
        buffer.len = zmq_msg_size(address(self.zmq_msg))

        buffer.obj = self
        buffer.readonly = 0
        buffer.format = "B"
        buffer.ndim = 1
        buffer.shape = address(buffer.len)
        buffer.strides = NULL
        buffer.suboffsets = NULL
        buffer.itemsize = 1
        buffer.internal = NULL

    def __getsegcount__(self, lenp: pointer(Py_ssize_t)) -> C.int:
        # required for getreadbuffer
        if lenp != NULL:
            lenp[0] = zmq_msg_size(address(self.zmq_msg))
        return 1

    def __getreadbuffer__(self, idx: Py_ssize_t, p: pointer(p_void)) -> Py_ssize_t:
        # old-style (buffer) interface
        data_c: p_char = NULL
        data_len_c: Py_ssize_t
        if idx != 0:
            raise SystemError("accessing non-existent buffer segment")
        # read-only, because we don't want to allow
        # editing of the message in-place
        data_c = cast(p_char, zmq_msg_data(address(self.zmq_msg)))
        data_len_c = zmq_msg_size(address(self.zmq_msg))
        if p != NULL:
            p[0] = cast(p_void, data_c)
        return data_len_c

    def __len__(self) -> size_t:
        """Return the length of the message in bytes."""
        sz: size_t = zmq_msg_size(address(self.zmq_msg))
        return sz

    @property
    def buffer(self):
        """A memoryview of the message contents."""
        _buffer = self._buffer and self._buffer()
        if _buffer is not None:
            return _buffer
        _buffer = memoryview(self)
        self._buffer = ref(_buffer)
        return _buffer

    @property
    def bytes(self):
        """The message content as a Python bytes object.

        The first time this property is accessed, a copy of the message
        contents is made. From then on that same copy of the message is
        returned.
        """
        if self._bytes is None:
            self._bytes = _copy_zmq_msg_bytes(address(self.zmq_msg))
        return self._bytes

    def get(self, option):
        """
        Get a Frame option or property.

        See the 0MQ API documentation for zmq_msg_get and zmq_msg_gets
        for details on specific options.

        .. versionadded:: libzmq-3.2
        .. versionadded:: 13.0

        .. versionchanged:: 14.3
            add support for zmq_msg_gets (requires libzmq-4.1)
            All message properties are strings.

        .. versionchanged:: 17.0
            Added support for `routing_id` and `group`.
            Only available if draft API is enabled
            with libzmq >= 4.2.
        """
        rc: C.int = 0
        property_c: p_char = NULL

        # zmq_msg_get
        if isinstance(option, int):
            rc = zmq_msg_get(address(self.zmq_msg), option)
            _check_rc(rc)
            return rc

        if option == 'routing_id':
            routing_id: uint32_t = zmq_msg_routing_id(address(self.zmq_msg))
            if routing_id == 0:
                _check_rc(-1)
            return routing_id
        elif option == 'group':
            buf = zmq_msg_group(address(self.zmq_msg))
            if buf == NULL:
                _check_rc(-1)
            return buf.decode('utf8')

        # zmq_msg_gets
        _check_version((4, 1), "get string properties")
        if isinstance(option, str):
            option = option.encode('utf8')

        if not isinstance(option, bytes):
            raise TypeError(f"expected str, got: {option!r}")

        property_c = option

        result: p_char = cast(p_char, zmq_msg_gets(address(self.zmq_msg), property_c))
        if result == NULL:
            _check_rc(-1)
        return result.decode('utf8')

    def set(self, option, value):
        """Set a Frame option.

        See the 0MQ API documentation for zmq_msg_set
        for details on specific options.

        .. versionadded:: libzmq-3.2
        .. versionadded:: 13.0
        .. versionchanged:: 17.0
            Added support for `routing_id` and `group`.
            Only available if draft API is enabled
            with libzmq >= 4.2.
        """
        rc: C.int

        if option == 'routing_id':
            routing_id: uint32_t = value
            rc = zmq_msg_set_routing_id(address(self.zmq_msg), routing_id)
            _check_rc(rc)
            return
        elif option == 'group':
            if isinstance(value, str):
                value = value.encode('utf8')
            rc = zmq_msg_set_group(address(self.zmq_msg), value)
            _check_rc(rc)
            return

        rc = zmq_msg_set(address(self.zmq_msg), option, value)
        _check_rc(rc)


@cclass
class Context:
    """
    Manage the lifecycle of a 0MQ context.

    Parameters
    ----------
    io_threads : int
        The number of IO threads.
    """

    def __init__(self, io_threads: C.int = 1, shadow: size_t = 0):
        self.handle = NULL
        self._pid = 0
        self._shadow = False

        if shadow:
            self.handle = cast(p_void, shadow)
            self._shadow = True
        else:
            self._shadow = False
            if ZMQ_VERSION_MAJOR >= 3:
                self.handle = zmq_ctx_new()
            else:
                self.handle = zmq_init(io_threads)

        if self.handle == NULL:
            raise ZMQError()

        rc: C.int = 0
        if ZMQ_VERSION_MAJOR >= 3 and not self._shadow:
            rc = zmq_ctx_set(self.handle, ZMQ_IO_THREADS, io_threads)
            _check_rc(rc)

        self.closed = False
        self._pid = getpid()

    @property
    def underlying(self):
        """The address of the underlying libzmq context"""
        return cast(size_t, self.handle)

    @C.cfunc
    @C.inline
    def _term(self) -> C.int:
        rc: C.int = 0
        if self.handle != NULL and not self.closed and getpid() == self._pid:
            with nogil:
                rc = zmq_ctx_destroy(self.handle)
        self.handle = NULL
        return rc

    def term(self):
        """
        Close or terminate the context.

        This can be called to close the context by hand. If this is not called,
        the context will automatically be closed when it is garbage collected.
        """
        rc: C.int = self._term()
        try:
            _check_rc(rc)
        except InterruptedSystemCall:
            # ignore interrupted term
            # see PEP 475 notes about close & EINTR for why
            pass

        self.closed = True

    def set(self, option: C.int, optval):
        """
        Set a context option.

        See the 0MQ API documentation for zmq_ctx_set
        for details on specific options.

        .. versionadded:: libzmq-3.2
        .. versionadded:: 13.0

        Parameters
        ----------
        option : int
            The option to set.  Available values will depend on your
            version of libzmq.  Examples include::

                zmq.IO_THREADS, zmq.MAX_SOCKETS

        optval : int
            The value of the option to set.
        """
        optval_int_c: C.int
        rc: C.int

        if self.closed:
            raise RuntimeError("Context has been destroyed")

        if not isinstance(optval, int):
            raise TypeError(f'expected int, got: {optval!r}')
        optval_int_c = optval
        rc = zmq_ctx_set(self.handle, option, optval_int_c)
        _check_rc(rc)

    def get(self, option: C.int):
        """
        Get the value of a context option.

        See the 0MQ API documentation for zmq_ctx_get
        for details on specific options.

        .. versionadded:: libzmq-3.2
        .. versionadded:: 13.0

        Parameters
        ----------
        option : int
            The option to get.  Available values will depend on your
            version of libzmq.  Examples include::

                zmq.IO_THREADS, zmq.MAX_SOCKETS

        Returns
        -------
        optval : int
            The value of the option as an integer.
        """
        rc: C.int

        if self.closed:
            raise RuntimeError("Context has been destroyed")

        rc = zmq_ctx_get(self.handle, option)
        _check_rc(rc, error_without_errno=False)
        return rc


# General utility functions


def zmq_errno():
    """Return the integer errno of the most recent zmq error."""
    return _zmq_errno()


def strerror(errno: C.int) -> str:
    """
    Return the error string given the error number.
    """
    str_e: bytes = zmq_strerror(errno)
    return str_e.decode("utf8", "replace")


def zmq_version_info() -> (int, int, int):
    """Return the version of ZeroMQ itself as a 3-tuple of ints."""
    major: C.int = 0
    minor: C.int = 0
    patch: C.int = 0
    _zmq_version(address(major), address(minor), address(patch))
    return (major, minor, patch)


def has(capability) -> bool:
    """Check for zmq capability by name (e.g. 'ipc', 'curve')

    .. versionadded:: libzmq-4.1
    .. versionadded:: 14.1
    """
    _check_version((4, 1), 'zmq.has')
    ccap: bytes
    if isinstance(capability, str):
        capability = capability.encode('utf8')
    ccap = capability
    return bool(zmq_has(ccap))


def curve_keypair():
    """generate a Z85 key pair for use with zmq.CURVE security

    Requires libzmq (≥ 4.0) to have been built with CURVE support.

    .. versionadded:: libzmq-4.0
    .. versionadded:: 14.0

    Returns
    -------
    (public, secret) : two bytestrings
        The public and private key pair as 40 byte z85-encoded bytestrings.
    """
    rc: C.int
    public_key = declare(char[64])
    secret_key = declare(char[64])
    _check_version((4, 0), "curve_keypair")
    # see huge comment in libzmq/src/random.cpp
    # about threadsafety of random initialization
    rc = zmq_curve_keypair(public_key, secret_key)
    _check_rc(rc)
    return public_key, secret_key


def curve_public(secret_key) -> bytes:
    """Compute the public key corresponding to a secret key for use
    with zmq.CURVE security

    Requires libzmq (≥ 4.2) to have been built with CURVE support.

    Parameters
    ----------
    private
        The private key as a 40 byte z85-encoded bytestring

    Returns
    -------
    bytestring
        The public key as a 40 byte z85-encoded bytestring
    """
    if isinstance(secret_key, str):
        secret_key = secret_key.encode('utf8')
    if not len(secret_key) == 40:
        raise ValueError('secret key must be a 40 byte z85 encoded string')

    rc: C.int
    public_key = declare(char[64])
    c_secret_key: pointer(char) = secret_key
    _check_version((4, 2), "curve_public")
    # see huge comment in libzmq/src/random.cpp
    # about threadsafety of random initialization
    rc = zmq_curve_public(public_key, c_secret_key)
    _check_rc(rc)
    return public_key[:40]


Message = Frame

__all__ = [
    'Frame',
    'Message',
    'has',
    'curve_keypair',
    'curve_public',
    'zmq_version_info',
    'zmq_errno',
    'strerror',
]
