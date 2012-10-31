import pytest

from zmq.cffi_core._cffi import zmq_version

def test_zmq_version_info():
    from zmq.cffi_core._cffi import zmq_version_info

    version = zmq_version_info()

    assert version[0] in (2, 3)

def test_zmq_init():
    from zmq.cffi_core._cffi import C

    ctx = C.zmq_init(1)

    assert ctx
    ret = C.zmq_term(ctx)

def test_zmq_term():
    from zmq.cffi_core._cffi import C

    ctx = C.zmq_init(1)
    ret = C.zmq_term(ctx)

    assert ret == 0

@pytest.mark.skipif('zmq_version == 2')
def test_zmq_ctx_destroy():
    from zmq.cffi_core._cffi import C, zmq_version

    ctx = C.zmq_init(1)
    ret = C.zmq_ctx_destroy(ctx)

    assert ret == 0

def test_zmq_socket():
    from zmq.cffi_core._cffi import C
    from zmq.cffi_core.constants import PUSH

    ctx = C.zmq_init(1)
    socket = C.zmq_socket(ctx, PUSH)

    assert socket

def test_zmq_socket_close():
    from zmq.cffi_core._cffi import C
    from zmq.cffi_core.constants import PUSH

    ctx = C.zmq_init(1)
    socket = C.zmq_socket(ctx, PUSH)

    ret = C.zmq_close(socket)

    assert ret == 0

def test_zmq_setsockopt():
    from zmq.cffi_core._cffi import C, ffi
    from zmq.cffi_core.constants import PUSH, IDENTITY

    ctx = C.zmq_init(1)
    socket = C.zmq_socket(ctx, PUSH)

    identity = ffi.new('char[3]', 'zmq')
    ret = C.zmq_setsockopt(socket, IDENTITY, ffi.cast('void*', identity), 3)
    assert ret == 0

def test_zmq_getsockopt():
    from zmq.cffi_core._cffi import C, ffi
    from zmq.cffi_core.constants import PUSH, IDENTITY

    ctx = C.zmq_init(1)
    socket = C.zmq_socket(ctx, PUSH)

    identity = ffi.new('char[]', 'zmq')
    ret = C.zmq_setsockopt(socket, IDENTITY, ffi.cast('void*', identity), 3)
    assert ret == 0

    option_len = ffi.new('unsigned long*', 3)
    option = ffi.new('char*')
    ret = C.zmq_getsockopt(socket,
                           IDENTITY,
                           ffi.cast('void*', option),
                           option_len)

    assert ret == 0
    assert ffi.string(ffi.cast('char*', option))[0] == "z"
    assert ffi.string(ffi.cast('char*', option))[1] == "m"
    assert ffi.string(ffi.cast('char*', option))[2] == "q"

def test_zmq_bind_connect():
    from zmq.cffi_core.constants import PAIR

    ctx = C.zmq_init(1)
    socket1 = C.zmq_socket(ctx, PAIR)
    r1 = C.zmq_bind(socket1, 'tcp://*:5555')

    assert r1 == 0

def test_zmq_bind_connect():
    from zmq.cffi_core._cffi import C, ffi
    from zmq.cffi_core.constants import PAIR

    ctx = C.zmq_init(1)

    socket1 = C.zmq_socket(ctx, PAIR)
    socket2 = C.zmq_socket(ctx, PAIR)

    r1 = C.zmq_bind(socket1, 'tcp://*:5555')
    r2 = C.zmq_connect(socket2, 'tcp://127.0.0.1:5555')

    assert r1 == 0
    assert r2 == 0

def test_zmq_msg_init():
    from zmq.cffi_core._cffi import C, ffi

    zmq_msg = ffi.new('zmq_msg_t*')

    assert zmq_msg

    C.zmq_msg_init(zmq_msg)

    assert zmq_msg

def test_zmq_msg_close():
    from zmq.cffi_core._cffi import C, ffi

    zmq_msg = ffi.new('zmq_msg_t*')
    C.zmq_msg_init(zmq_msg)
    ret = C.zmq_msg_close(zmq_msg)

    assert ret == 0

def test_zmq_msg_init_size():
    from zmq.cffi_core._cffi import C, ffi

    zmq_msg = ffi.new('zmq_msg_t*')

    assert zmq_msg

    C.zmq_msg_init_size(zmq_msg, 10)

    assert zmq_msg

def test_zmq_msg_init_data():
    from zmq.cffi_core._cffi import C, ffi

    zmq_msg = ffi.new('zmq_msg_t*')
    assert zmq_msg

    message = ffi.new('char[5]', 'Hello')
    C.zmq_msg_init_data(zmq_msg, ffi.cast('void*', message), 5, ffi.NULL,
                                                                ffi.NULL)

    assert zmq_msg

def test_zmq_msg_close():
    from zmq.cffi_core._cffi import C, ffi

    zmq_msg = ffi.new('zmq_msg_t*')
    assert zmq_msg

    message = ffi.new('char[]', 'Hello')
    C.zmq_msg_init_data(zmq_msg, ffi.cast('void*', message), 5, ffi.NULL,
                                                                ffi.NULL)

    assert zmq_msg

    ret = C.zmq_msg_close(zmq_msg)
    assert ret == 0

def test_zmq_msg_data():
    from zmq.cffi_core._cffi import C, ffi

    zmq_msg = ffi.new('zmq_msg_t*')
    assert zmq_msg

    message = ffi.new('char[]', 'Hello')
    C.zmq_msg_init_data(zmq_msg, ffi.cast('void*', message), 5, ffi.NULL,
                                                                ffi.NULL)

    assert zmq_msg

    data = C.zmq_msg_data(zmq_msg)
    assert ffi.string(ffi.cast("char*", data)) == 'Hello'


def test_zmq_send():
    from zmq.cffi_core.constants import PAIR, NOBLOCK
    from zmq.cffi_core._cffi import C, ffi, zmq_version

    zmq_msg = ffi.new('zmq_msg_t*')

    message = ffi.new('char[5]', 'Hello')
    C.zmq_msg_init_data(zmq_msg, ffi.cast('void*', message), 5, ffi.NULL,
                                                                ffi.NULL)

    ctx = C.zmq_init(1)

    socket1 = C.zmq_socket(ctx, PAIR)
    socket2 = C.zmq_socket(ctx, PAIR)

    r1 = C.zmq_bind(socket1, 'tcp://*:5555')
    r2 = C.zmq_connect(socket2, 'tcp://127.0.0.1:5555')

    if zmq_version == 2:
        ret = C.zmq_send(socket2, zmq_msg, 0)
        assert ret == 0
    else:
        ret = C.zmq_sendmsg(socket2, zmq_msg, 0)
        assert ret == 5

    assert C.zmq_close(socket1) == 0
    assert C.zmq_close(socket2) == 0
    assert C.zmq_term(ctx) == 0

def test_zmq_recv():
    from zmq.cffi_core.constants import REQ, REP, NOBLOCK
    from zmq.cffi_core._cffi import C, ffi, zmq_version

    ctx = C.zmq_init(1)

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

    zmq_msg2 = ffi.new('zmq_msg_t*')
    C.zmq_msg_init(zmq_msg2)

    if zmq_version == 2:
        ret = C.zmq_send(sender, zmq_msg, 0)
        ret2 = C.zmq_recv(receiver, zmq_msg2, 0)
        assert ret == ret2 == 0
    else:
        ret = C.zmq_sendmsg(sender, zmq_msg, 0)
        ret2 = C.zmq_recvmsg(receiver, zmq_msg2, 0)
        assert ret == ret2 == 5

    assert 5 == C.zmq_msg_size(zmq_msg2)
    assert "Hello" == ffi.string(ffi.cast('char*', C.zmq_msg_data(zmq_msg2)))

    assert C.zmq_close(sender) == 0
    assert C.zmq_close(receiver) == 0
    assert C.zmq_term(ctx) == 0

def test_zmq_poll():
    from zmq.cffi_core.constants import REQ, REP, NOBLOCK, POLLIN, POLLOUT
    from zmq.cffi_core._cffi import C, ffi, zmq_version

    ctx = C.zmq_init(1)

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

    if zmq_version == 2:
        ret = C.zmq_send(sender, zmq_msg, 0)
        assert ret == 0
    else:
        ret = C.zmq_sendmsg(sender, zmq_msg, 0)
        assert ret == 5


    assert C.zmq_msg_close(zmq_msg) == 0

    import time
    time.sleep(0.2)

    ret = C.zmq_poll(receiver_pollitem, 1, 0)
    assert ret == 1

    assert int(receiver_pollitem.revents) & POLLIN
    assert not int(receiver_pollitem.revents) & POLLOUT

    zmq_msg2 = ffi.new('zmq_msg_t*')
    C.zmq_msg_init(zmq_msg2)

    if zmq_version == 2:
        ret_recv = C.zmq_recv(receiver, zmq_msg2, 0)
        assert ret_recv == 0
    else:
        ret_recv = C.zmq_recvmsg(receiver, zmq_msg2, 0)
        assert ret_recv == 5

    assert 5 == C.zmq_msg_size(zmq_msg2)
    assert "Hello" == ffi.string(ffi.cast('char*', C.zmq_msg_data(zmq_msg2)))

    #assert C.zmq_msg_close(zmq_msg2) == 0

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

    if zmq_version == 2:
        ret_send = C.zmq_send(receiver, zmq_msg_again, 0)
        assert ret_send == 0
    else:
        ret_send = C.zmq_sendmsg(receiver, zmq_msg_again, 0)
        assert ret_send == 11

    import time
    time.sleep(0.2)

    ret = C.zmq_poll(sender_pollitem, 1, 0)

    assert ret >= 0
    assert int(sender_pollitem.revents) & POLLIN

    if zmq_version == 2:
        ret_recv = C.zmq_recv(sender, zmq_msg2, 0)
        assert ret_recv == 0
    else:
        ret_recv = C.zmq_recvmsg(sender, zmq_msg2, 0)
        assert ret_recv == 11

    assert 11 == C.zmq_msg_size(zmq_msg2)
    assert "Hello Again" == ffi.buffer(C.zmq_msg_data(zmq_msg2), int(C.zmq_msg_size(zmq_msg2)))[:]
    assert C.zmq_close(sender) == 0
    assert C.zmq_close(receiver) == 0
    assert C.zmq_term(ctx) == 0
