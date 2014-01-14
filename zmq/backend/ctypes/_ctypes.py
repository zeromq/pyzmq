# coding: utf-8
"""ctypes declaration for zmqlib"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2014 Pawel Jasinski
#  Derived from pyzmq-ctypes Copyright (C) 2011 Daniel Holth
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from __future__ import absolute_import, print_function

from ctypes import *

size_t = c_size_t

try:
    libzmq = windll.libzmq
except OSError:
    import sys
    print("Failed to load libzmq.dll")
    sys.exit(1)

class zmq_msg_t(Structure):
     _fields_ = [ ('x', c_ubyte*32) ]

class zmq_pollitem_t(Structure):
    _fields_ = [
            ('socket', c_void_p),
            ('fd', c_int),
            ('events', c_short),
            ('revents', c_short)
            ]

EMPTY_STRING = create_string_buffer('')

libzmq.zmq_bind.restype = c_int
libzmq.zmq_bind.argtypes = [c_void_p, c_char_p]

libzmq.zmq_close.restype = c_int
libzmq.zmq_close.argtypes = [c_void_p]
libzmq.zmq_connect.restype = c_int
libzmq.zmq_connect.argtypes = [c_void_p, c_char_p]
try:
    libzmq.zmq_curve_keypair.restype = c_int
    libzmq.zmq_curve_keypair.argtypes = [c_void_p, c_char_p]
except AttributeError:
    # new in 4.x
    pass

libzmq.zmq_ctx_destroy.restype = c_int
libzmq.zmq_ctx_destroy.argtypes = [c_void_p]
libzmq.zmq_ctx_get.restype = c_int
libzmq.zmq_ctx_get.argtypes = [c_void_p, c_int]
libzmq.zmq_ctx_new.restype = c_void_p
libzmq.zmq_ctx_new.argtypes = None
libzmq.zmq_ctx_set.restype = c_int
libzmq.zmq_ctx_set.argtypes = [c_void_p, c_int, c_int]
try:
    libzmq.zmq_ctx_term.restype = c_int
    libzmq.zmq_ctx_term.argtypes = [c_void_p ]
except AttributeError:
    # new in 4.x
    pass

libzmq.zmq_disconnect.restype = c_int
libzmq.zmq_disconnect.argtypes = [c_void_p, c_char_p]

libzmq.zmq_errno.argtypes = []

libzmq.zmq_getsockopt.restype = c_int
# parameter checking is not happy with the next line
#libzmq.zmq_getsockopt.argtypes = [c_void_p, c_int, c_void_p, POINTER(size_t)]

libzmq.zmq_init.restype = c_void_p
libzmq.zmq_init.argtypes = [c_int]

libzmq.zmq_msg_close.restype = c_int
libzmq.zmq_msg_close.argtypes = [POINTER(zmq_msg_t)]
libzmq.zmq_msg_copy.argtypes = [POINTER(zmq_msg_t), POINTER(zmq_msg_t)]
libzmq.zmq_msg_copy.restype = c_int
libzmq.zmq_msg_data.restype = c_void_p
libzmq.zmq_msg_data.argtypes = [POINTER(zmq_msg_t)]
libzmq.zmq_msg_init.argtypes = [POINTER(zmq_msg_t)]
libzmq.zmq_msg_init.restype = c_int
libzmq.zmq_msg_init_size.restype = c_int
libzmq.zmq_msg_init_size.argtypes = [POINTER(zmq_msg_t), size_t]
libzmq.zmq_msg_init_data.restype = c_int
libzmq.zmq_msg_init_data.argtypes = [POINTER(zmq_msg_t), c_void_p, size_t, c_void_p, c_void_p]
libzmq.zmq_msg_move.argtypes = [POINTER(zmq_msg_t), POINTER(zmq_msg_t)]
libzmq.zmq_msg_recv.restype = c_int
libzmq.zmq_msg_recv.argtypes = [POINTER(zmq_msg_t), c_void_p, c_int]
libzmq.zmq_msg_send.restype = c_int
libzmq.zmq_msg_send.argtypes = [POINTER(zmq_msg_t), c_void_p, c_int]
libzmq.zmq_msg_size.restype = size_t
libzmq.zmq_msg_size.argtypes = [POINTER(zmq_msg_t)]

libzmq.zmq_poll.restype = c_int
libzmq.zmq_poll.argtypes = [POINTER(zmq_pollitem_t), c_int, c_long]

libzmq.zmq_recv.restype = c_int
libzmq.zmq_recv.argtypes = [c_void_p, POINTER(zmq_msg_t), c_int]

libzmq.zmq_send.restype = c_int
libzmq.zmq_send.argtypes = [c_void_p, POINTER(zmq_msg_t), c_int]
libzmq.zmq_setsockopt.restype = c_int
# parameter checking is not happy with the next line
#libzmq.zmq_setsockopt.argtypes = [c_void_p, c_int, c_void_p, size_t]
libzmq.zmq_sleep.restype = c_void_p
libzmq.zmq_sleep.argtypes = [c_int]
libzmq.zmq_socket.restype = c_void_p
libzmq.zmq_socket.argtypes = [c_void_p, c_int]
libzmq.zmq_socket_monitor.restype = c_int
libzmq.zmq_socket_monitor.argtypes = [c_void_p, c_char_p, c_int]
libzmq.zmq_strerror.restype = c_char_p
libzmq.zmq_strerror.argtypes = [c_int]
libzmq.zmq_stopwatch_start.restype = c_void_p
libzmq.zmq_stopwatch_start.argtypes = None
libzmq.zmq_stopwatch_stop.restype = c_ulong    
libzmq.zmq_stopwatch_stop.argtypes = [c_void_p]

libzmq.zmq_term.restype = c_int
libzmq.zmq_term.argtypes = [c_void_p]

libzmq.zmq_unbind.restype = c_int
libzmq.zmq_unbind.argtypes = [c_void_p, c_char_p]

__all__ = [ 'libzmq', 'zmq_msg_t', 'zmq_pollitem_t', 'EMPTY_STRING' ]
