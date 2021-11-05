#cython: language_level=3str

"""Using pyzmq from Cython"""


cimport numpy as np
from cpython cimport array
from libc.string cimport memcpy

from zmq cimport Socket, libzmq

import array
import sys
import time
from threading import Thread

import zmq


cpdef cython_sender(str url, int n):
    """Use entirely low-level libzmq APIs to send messages"""
    cdef void* ctx
    cdef void* s
    cdef int rc

    # create context and socket with libzmq
    ctx = libzmq.zmq_ctx_new()
    assert ctx != NULL, zmq.strerror(zmq.zmq_errno())
    s = libzmq.zmq_socket(ctx, libzmq.ZMQ_PUSH)
    assert s != NULL, zmq.strerror(zmq.zmq_errno())
    cdef bytes burl = url.encode("utf8")
    rc = libzmq.zmq_connect(s, burl)
    assert rc >= 0, zmq.strerror(zmq.zmq_errno())

    cdef libzmq.zmq_msg_t msg
    cdef array.array buf = array.array('i', [1])
    cdef int sz = 4
    start = time.perf_counter()
    for i in range(n):
        buf.data.as_ints[0] = i
        libzmq.zmq_msg_init_size(&msg, sz)
        memcpy(libzmq.zmq_msg_data(&msg), buf.data.as_chars, sz)
        libzmq.zmq_msg_send(&msg, s, 0)
        libzmq.zmq_msg_close(&msg)
    stop = time.perf_counter()
    # send a final message with the timer measurement
    buf = array.array('d', [stop - start])
    sz = 8
    libzmq.zmq_msg_init_size(&msg, sz)
    memcpy(libzmq.zmq_msg_data(&msg), buf.data.as_chars, sz)
    libzmq.zmq_msg_send(&msg, s, 0)
    libzmq.zmq_msg_close(&msg)

    # cleanup sockets
    libzmq.zmq_close(s)
    libzmq.zmq_term(ctx)


cpdef mixed_receiver(Socket s, int n):
    """Use mixed Cython APIs to recv messages"""
    cdef void* c_sock = s.handle
    for i in range(n):
        msg = s.recv()
