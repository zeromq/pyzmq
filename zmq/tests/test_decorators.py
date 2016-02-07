import threading
import zmq

from nose.tools import raises
from time import sleep
from zmq.decorators import context, socket


@context()
def test_ctx(ctx):
    assert isinstance(ctx, zmq.Context), ctx


def test_ctx_orig_args():
    @context()
    def f(foo, bar, ctx, baz=None):
        assert isinstance(ctx, zmq.Context), ctx
        assert foo == 42
        assert bar is True
        assert baz == 'mock'

    f(42, True, baz='mock')


@context('myctx')
def test_ctx_arg_naming(myctx):
    assert isinstance(myctx, zmq.Context), myctx


@context('ctx', 5)
def test_ctx_args(ctx):
    assert isinstance(ctx, zmq.Context), ctx
    assert ctx.IO_THREADS == 5, ctx.IO_THREADS


@context('ctx', io_threads=5)
def test_ctx_arg_kwarg(ctx):
    assert isinstance(ctx, zmq.Context), ctx
    assert ctx.IO_THREADS == 5, ctx.IO_THREADS


@context(name='myctx')
def test_ctx_kw_naming(myctx):
    assert isinstance(myctx, zmq.Context), myctx


@context(name='ctx', io_threads=5)
def test_ctx_kwargs(ctx):
    assert isinstance(ctx, zmq.Context), ctx
    assert ctx.IO_THREADS == 5, ctx.IO_THREADS


@context(name='ctx', io_threads=5)
def test_ctx_kwargs_default(ctx=None):
    assert isinstance(ctx, zmq.Context), ctx
    assert ctx.IO_THREADS == 5, ctx.IO_THREADS


@raises(TypeError)
@context(name='ctx')
def test_ctx_keyword_miss(other_name):
    pass  # the keyword ``ctx`` not found


@raises(TypeError)
def test_multi_assign():
    @context(name='ctx')
    def f(ctx):
        pass  # explosion
    f('mock')


def test_ctx_reinit():
    result = {'foo': None, 'bar': None}

    @context()
    def f(key, lock, ctx):
        assert isinstance(ctx, zmq.Context), ctx

        sleep(0.5)
        with lock:
            result[key] = id(ctx)

    lock = threading.Lock()
    foo_t = threading.Thread(target=f, args=('foo', lock))
    bar_t = threading.Thread(target=f, args=('bar', lock))

    foo_t.start()
    bar_t.start()

    foo_t.join()
    bar_t.join()

    assert result['foo'] is not None, result
    assert result['bar'] is not None, result
    assert result['foo'] != result['bar'], result


@context()
@socket(zmq.PUB)
def test_ctx_skt(skt, ctx):
    assert isinstance(skt, zmq.Socket), skt
    assert isinstance(ctx, zmq.Context), ctx
    assert skt.type == zmq.PUB


@context()
@socket('myskt', zmq.PUB)
def test_skt_name(ctx, myskt):
    assert isinstance(myskt, zmq.Socket), myskt
    assert isinstance(ctx, zmq.Context), ctx
    assert myskt.type == zmq.PUB


@context()
@socket(zmq.PUB, name='myskt')
def test_skt_kwarg(ctx, myskt):
    assert isinstance(myskt, zmq.Socket), myskt
    assert isinstance(ctx, zmq.Context), ctx
    assert myskt.type == zmq.PUB


@context('ctx')
@socket('skt', zmq.PUB, context_name='ctx')
def test_ctx_skt(ctx, skt):
    assert isinstance(skt, zmq.Socket), skt
    assert isinstance(ctx, zmq.Context), ctx
    assert skt.type == zmq.PUB


@socket(zmq.PUB)
def test_skt_default_ctx(skt):
    assert isinstance(skt, zmq.Socket), skt
    assert skt.context is zmq.Context.instance()
    assert skt.type == zmq.PUB


def test_skt_reinit():
    result = {'foo': None, 'bar': None}

    @socket(zmq.PUB)
    def f(key, lock, skt):
        assert isinstance(skt, zmq.Socket), skt

        sleep(0.5)
        with lock:
            result[key] = id(skt)

    lock = threading.Lock()
    foo_t = threading.Thread(target=f, args=('foo', lock))
    bar_t = threading.Thread(target=f, args=('bar', lock))

    foo_t.start()
    bar_t.start()

    foo_t.join()
    bar_t.join()

    assert result['foo'] is not None, result
    assert result['bar'] is not None, resule
    assert result['foo'] != result['bar'], result


def test_ctx_skt_reinit():
    result = {'foo': {'ctx': None, 'skt': None},
              'bar': {'ctx': None, 'skt': None}}

    @context()
    @socket(zmq.PUB)
    def f(key, lock, ctx, skt):
        assert isinstance(ctx, zmq.Context), ctx
        assert isinstance(skt, zmq.Socket), skt

        sleep(0.5)

        with lock:
            result[key]['ctx'] = id(ctx)
            result[key]['skt'] = id(skt)

    lock = threading.Lock()
    foo_t = threading.Thread(target=f, args=('foo', lock))
    bar_t = threading.Thread(target=f, args=('bar', lock))

    foo_t.start()
    bar_t.start()

    foo_t.join()
    bar_t.join()

    assert result['foo']['ctx'] is not None, result
    assert result['foo']['skt'] is not None, result
    assert result['bar']['ctx'] is not None, result
    assert result['bar']['skt'] is not None, result
    assert result['foo']['ctx'] != result['bar']['ctx'], result
    assert result['foo']['skt'] != result['bar']['skt'], result


@raises(TypeError)
@context()
@socket('myskt')
def test_skt_type_miss(ctx, myskt):
    pass  # the socket type is missing


@socket(zmq.PUB)
@socket(zmq.SUB)
@socket(zmq.PUSH)
def test_multi_skts(pub, sub, push):
    assert isinstance(pub, zmq.Socket), pub
    assert isinstance(sub, zmq.Socket), sub
    assert isinstance(push, zmq.Socket), push

    assert pub.context is zmq.Context.instance()
    assert sub.context is zmq.Context.instance()
    assert push.context is zmq.Context.instance()

    assert pub.type == zmq.PUB
    assert sub.type == zmq.SUB
    assert push.type == zmq.PUSH


@context()
@socket(zmq.PUB)
@socket(zmq.SUB)
@socket(zmq.PUSH)
def test_multi_skts_single_ctx(ctx, pub, sub, push):
    assert isinstance(ctx, zmq.Context), ctx
    assert isinstance(pub, zmq.Socket), pub
    assert isinstance(sub, zmq.Socket), sub
    assert isinstance(push, zmq.Socket), push

    assert pub.context is ctx
    assert sub.context is ctx
    assert push.context is ctx

    assert pub.type == zmq.PUB
    assert sub.type == zmq.SUB
    assert push.type == zmq.PUSH


@socket('foo', zmq.PUSH)
@socket('bar', zmq.SUB)
@socket('baz', zmq.PUB)
def test_multi_skts_with_name(foo, bar, baz):
    assert isinstance(foo, zmq.Socket), foo
    assert isinstance(bar, zmq.Socket), bar
    assert isinstance(baz, zmq.Socket), baz

    assert foo.context is zmq.Context.instance()
    assert bar.context is zmq.Context.instance()
    assert baz.context is zmq.Context.instance()

    assert foo.type == zmq.PUSH
    assert bar.type == zmq.SUB
    assert baz.type == zmq.PUB


def test_func_return():
    @context()
    def f(ctx):
        assert isinstance(ctx, zmq.Context), ctx
        return 'something'

    assert f() == 'something'


class TestMethodDecorators():
    @context()
    @socket(zmq.PUB)
    @socket(zmq.SUB)
    def test_multi_skts_method(self, ctx, pub, sub, foo='bar'):
        assert isinstance(self, TestMethodDecorators), self
        assert isinstance(ctx, zmq.Context), ctx
        assert isinstance(pub, zmq.Socket), pub
        assert isinstance(sub, zmq.Socket), sub
        assert foo == 'bar'

        assert pub.context is ctx
        assert sub.context is ctx

        assert pub.type is zmq.PUB
        assert sub.type is zmq.SUB

    def test_multi_skts_method_other_args(self):
        @socket(zmq.PUB)
        @socket(zmq.SUB)
        def f(foo, pub, sub, bar=None):
            assert isinstance(pub, zmq.Socket), pub
            assert isinstance(sub, zmq.Socket), sub

            assert foo == 'mock'
            assert bar == 'fake'

            assert pub.context is zmq.Context.instance()
            assert sub.context is zmq.Context.instance()

            assert pub.type is zmq.PUB
            assert sub.type is zmq.SUB

        f('mock', bar='fake')
