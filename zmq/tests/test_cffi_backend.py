# -*- coding: utf8 -*-

import sys
import time

from unittest import TestCase

from zmq.tests import BaseZMQTestCase, SkipTest

try:
    from zmq.backend.cffi import (
        zmq_version_info,
        PUSH, PULL, IDENTITY,
        REQ, REP, POLLIN, POLLOUT,
    )
    from zmq.backend.cffi._cffi import ffi, C
    have_ffi_backend = True
except ImportError:
    have_ffi_backend = False


class TestCFFIBackend(TestCase):
    
    def setUp(self):
        if not have_ffi_backend or not 'PyPy' in sys.version:
            raise SkipTest('PyPy Tests Only')

    def test_zmq_version_info(self):
        version = zmq_version_info()

        assert version[0] in range(2,11)

    def test_zmq_ctx_new_destroy(self):
        ctx = C.zmq_ctx_new()

        assert ctx != ffi.NULL
        assert 0 == C.zmq_ctx_destroy(ctx)

    def test_zmq_socket_open_close(self):
        ctx = C.zmq_ctx_new()
        socket = C.zmq_socket(ctx, PUSH)

        assert ctx != ffi.NULL
        assert ffi.NULL != socket
        assert 0 == C.zmq_close(socket)
        assert 0 == C.zmq_ctx_destroy(ctx)

    def test_zmq_setsockopt(self):
        ctx = C.zmq_ctx_new()
        socket = C.zmq_socket(ctx, PUSH)

        identity = ffi.new('char[3]', 'zmq')
        ret = C.zmq_setsockopt(socket, IDENTITY, ffi.cast('void*', identity), 3)

        assert ret == 0
        assert ctx != ffi.NULL
        assert ffi.NULL != socket
        assert 0 == C.zmq_close(socket)
        assert 0 == C.zmq_ctx_destroy(ctx)

    def test_zmq_getsockopt(self):
        ctx = C.zmq_ctx_new()
        socket = C.zmq_socket(ctx, PUSH)

        identity = ffi.new('char[]', 'zmq')
        ret = C.zmq_setsockopt(socket, IDENTITY, ffi.cast('void*', identity), 3)
        assert ret == 0

        option_len = ffi.new('size_t*', 3)
        option = ffi.new('char*')
        ret = C.zmq_getsockopt(socket,
                            IDENTITY,
                            ffi.cast('void*', option),
                            option_len)

        assert ret == 0
        assert ffi.string(ffi.cast('char*', option))[0] == "z"
        assert ffi.string(ffi.cast('char*', option))[1] == "m"
        assert ffi.string(ffi.cast('char*', option))[2] == "q"
        assert ctx != ffi.NULL
        assert ffi.NULL != socket
        assert 0 == C.zmq_close(socket)
        assert 0 == C.zmq_ctx_destroy(ctx)

    def test_zmq_bind(self):
        ctx = C.zmq_ctx_new()
        socket = C.zmq_socket(ctx, 8)

        assert 0 == C.zmq_bind(socket, 'tcp://*:4444')
        assert ctx != ffi.NULL
        assert ffi.NULL != socket
        assert 0 == C.zmq_close(socket)
        assert 0 == C.zmq_ctx_destroy(ctx)

    def test_zmq_bind_connect(self):
        ctx = C.zmq_ctx_new()

        socket1 = C.zmq_socket(ctx, PUSH)
        socket2 = C.zmq_socket(ctx, PULL)

        assert 0 == C.zmq_bind(socket1, 'tcp://*:4444')
        assert 0 == C.zmq_connect(socket2, 'tcp://127.0.0.1:4444')
        assert ctx != ffi.NULL
        assert ffi.NULL != socket1
        assert ffi.NULL != socket2
        assert 0 == C.zmq_close(socket1)
        assert 0 == C.zmq_close(socket2)
        assert 0 == C.zmq_ctx_destroy(ctx)

    def test_zmq_msg_init_close(self):
        zmq_msg = ffi.new('zmq_msg_t*')

        assert ffi.NULL != zmq_msg
        assert 0 == C.zmq_msg_init(zmq_msg)
        assert 0 == C.zmq_msg_close(zmq_msg)

    def test_zmq_msg_init_size(self):
        zmq_msg = ffi.new('zmq_msg_t*')

        assert ffi.NULL != zmq_msg
        assert 0 == C.zmq_msg_init_size(zmq_msg, 10)
        assert 0 == C.zmq_msg_close(zmq_msg)

    def test_zmq_msg_init_data(self):
        zmq_msg = ffi.new('zmq_msg_t*')
        message = ffi.new('char[5]', 'Hello')

        assert 0 == C.zmq_msg_init_data(zmq_msg,
                                        ffi.cast('void*', message),
                                        5,
                                        ffi.NULL,
                                        ffi.NULL)

        assert ffi.NULL != zmq_msg
        assert 0 == C.zmq_msg_close(zmq_msg)

    def test_zmq_msg_data(self):
        zmq_msg = ffi.new('zmq_msg_t*')
        message = ffi.new('char[]', 'Hello')
        assert 0 == C.zmq_msg_init_data(zmq_msg,
                                        ffi.cast('void*', message),
                                        5,
                                        ffi.NULL,
                                        ffi.NULL)

        data = C.zmq_msg_data(zmq_msg)

        assert ffi.NULL != zmq_msg
        assert ffi.string(ffi.cast("char*", data)) == 'Hello'
        assert 0 == C.zmq_msg_close(zmq_msg)


    def test_zmq_send(self):
        ctx = C.zmq_ctx_new()

        sender = C.zmq_socket(ctx, REQ)
        receiver = C.zmq_socket(ctx, REP)

        assert 0 == C.zmq_bind(receiver, 'tcp://*:7777')
        assert 0 == C.zmq_connect(sender, 'tcp://127.0.0.1:7777')

        time.sleep(0.1)

        zmq_msg = ffi.new('zmq_msg_t*')
        message = ffi.new('char[5]', 'Hello')

        C.zmq_msg_init_data(zmq_msg,
                            ffi.cast('void*', message),
                            ffi.cast('size_t', 5),
                            ffi.NULL,
                            ffi.NULL)

        assert 5 == C.zmq_msg_send(zmq_msg, sender, 0)
        assert 0 == C.zmq_msg_close(zmq_msg)
        assert C.zmq_close(sender) == 0
        assert C.zmq_close(receiver) == 0
        assert C.zmq_ctx_destroy(ctx) == 0

    def test_zmq_recv(self):
        ctx = C.zmq_ctx_new()

        sender = C.zmq_socket(ctx, REQ)
        receiver = C.zmq_socket(ctx, REP)

        assert 0 == C.zmq_bind(receiver, 'tcp://*:2222')
        assert 0 == C.zmq_connect(sender, 'tcp://127.0.0.1:2222')

        time.sleep(0.1)

        zmq_msg = ffi.new('zmq_msg_t*')
        message = ffi.new('char[5]', 'Hello')

        C.zmq_msg_init_data(zmq_msg,
                            ffi.cast('void*', message),
                            ffi.cast('size_t', 5),
                            ffi.NULL,
                            ffi.NULL)

        zmq_msg2 = ffi.new('zmq_msg_t*')
        C.zmq_msg_init(zmq_msg2)

        assert 5 == C.zmq_msg_send(zmq_msg, sender, 0)
        assert 5 == C.zmq_msg_recv(zmq_msg2, receiver, 0)
        assert 5 == C.zmq_msg_size(zmq_msg2)
        assert b"Hello" == ffi.buffer(C.zmq_msg_data(zmq_msg2),
                                      C.zmq_msg_size(zmq_msg2))[:]
        assert C.zmq_close(sender) == 0
        assert C.zmq_close(receiver) == 0
        assert C.zmq_ctx_destroy(ctx) == 0

    def test_zmq_poll(self):
        ctx = C.zmq_ctx_new()

        sender = C.zmq_socket(ctx, REQ)
        receiver = C.zmq_socket(ctx, REP)

        r1 = C.zmq_bind(receiver, 'tcp://*:3333')
        r2 = C.zmq_connect(sender, 'tcp://127.0.0.1:3333')

        zmq_msg = ffi.new('zmq_msg_t*')
        message = ffi.new('char[5]', 'Hello')

        C.zmq_msg_init_data(zmq_msg,
                            ffi.cast('void*', message),
                            ffi.cast('size_t', 5),
                            ffi.NULL,
                            ffi.NULL)

        receiver_pollitem = ffi.new('zmq_pollitem_t*')
        receiver_pollitem.socket = receiver
        receiver_pollitem.fd = 0
        receiver_pollitem.events = POLLIN | POLLOUT
        receiver_pollitem.revents = 0

        ret = C.zmq_poll(ffi.NULL, 0, 0)
        assert ret == 0

        ret = C.zmq_poll(receiver_pollitem, 1, 0)
        assert ret == 0

        ret = C.zmq_msg_send(zmq_msg, sender, 0)
        print(ffi.string(C.zmq_strerror(C.zmq_errno())))
        assert ret == 5

        time.sleep(0.2)

        ret = C.zmq_poll(receiver_pollitem, 1, 0)
        assert ret == 1

        assert int(receiver_pollitem.revents) & POLLIN
        assert not int(receiver_pollitem.revents) & POLLOUT

        zmq_msg2 = ffi.new('zmq_msg_t*')
        C.zmq_msg_init(zmq_msg2)

        ret_recv = C.zmq_msg_recv(zmq_msg2, receiver, 0)
        assert ret_recv == 5

        assert 5 == C.zmq_msg_size(zmq_msg2)
        assert b"Hello" == ffi.buffer(C.zmq_msg_data(zmq_msg2),
                                    C.zmq_msg_size(zmq_msg2))[:]

        sender_pollitem = ffi.new('zmq_pollitem_t*')
        sender_pollitem.socket = sender
        sender_pollitem.fd = 0
        sender_pollitem.events = POLLIN | POLLOUT
        sender_pollitem.revents = 0

        ret = C.zmq_poll(sender_pollitem, 1, 0)
        assert ret == 0

        zmq_msg_again = ffi.new('zmq_msg_t*')
        message_again = ffi.new('char[11]', 'Hello Again')

        C.zmq_msg_init_data(zmq_msg_again,
                            ffi.cast('void*', message_again),
                            ffi.cast('size_t', 11),
                            ffi.NULL,
                            ffi.NULL)

        assert 11 == C.zmq_msg_send(zmq_msg_again, receiver, 0)

        time.sleep(0.2)

        assert 0 <= C.zmq_poll(sender_pollitem, 1, 0)
        assert int(sender_pollitem.revents) & POLLIN
        assert 11 == C.zmq_msg_recv(zmq_msg2, sender, 0)
        assert 11 == C.zmq_msg_size(zmq_msg2)
        assert b"Hello Again" == ffi.buffer(C.zmq_msg_data(zmq_msg2),
                                            int(C.zmq_msg_size(zmq_msg2)))[:]
        assert 0 == C.zmq_close(sender)
        assert 0 == C.zmq_close(receiver)
        assert 0 == C.zmq_ctx_destroy(ctx)
        assert 0 == C.zmq_msg_close(zmq_msg)
        assert 0 == C.zmq_msg_close(zmq_msg2)
        assert 0 == C.zmq_msg_close(zmq_msg_again)

    def test_zmq_stopwatch_functions(self):
        stopwatch = C.zmq_stopwatch_start()
        ret = C.zmq_stopwatch_stop(stopwatch)

        assert ffi.NULL != stopwatch
        assert 0 < int(ret)

    def test_zmq_sleep(self):
        try:
            C.zmq_sleep(1)
        except Exception as e:
            raise AssertionError("Error executing zmq_sleep(int)")

