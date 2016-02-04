import zmq

from nose.tools import raises
from zmq.decorators import context, socket


@context()
def test_ctx(ctx):
    assert isinstance(ctx, zmq.Context), ctx


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
def test_mulit_assign():
    @context(name='ctx')
    def f(ctx):
        pass  # explosion
    f('mock')


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


@raises(TypeError)
@socket(zmq.PUB)
def test_ctx_miss(skt):
    pass  # context not found


@raises(TypeError)
@context()
@socket('myskt')
def test_skt_type_miss(ctx, myskt):
    pass  # the socket type is missing
