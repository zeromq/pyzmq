(eventloop)=

# Eventloops and PyZMQ

As of pyzmq 17, integrating pyzmq with eventloops should work without any pre-configuration.
Due to the use of an edge-triggered file descriptor,
this has been known to have issues, so please report problems with eventloop integration.

(asyncio)=

## AsyncIO

PyZMQ 15 adds support for {mod}`asyncio` via {mod}`zmq.asyncio`, containing a Socket subclass
that returns {py:class}`asyncio.Future` objects for use in {py:mod}`asyncio` coroutines.
To use this API, import {class}`zmq.asyncio.Context`.
Sockets created by this Context will return Futures from any would-be blocking method.

```python
import asyncio
import zmq
from zmq.asyncio import Context

ctx = Context.instance()


async def recv():
    s = ctx.socket(zmq.SUB)
    s.connect("tcp://127.0.0.1:5555")
    s.subscribe(b"")
    while True:
        msg = await s.recv_multipart()
        print("received", msg)
    s.close()
```

## Tornado IOLoop

[Tornado] adds some utility on top of asyncio.
You can use {mod}`zmq.asyncio` socket in a tornado application without any special handling.

We have adapted tornado's {class}`~.tornado.iostream.IOStream` class into {class}`~.ZMQStream` for
handling message events on ØMQ sockets. A ZMQStream object works much like a Socket object,
but instead of calling {meth}`~.zmq.Socket.recv` directly, you register a callback with
{meth}`~.ZMQStream.on_recv_stream`, which will be called with the result of `~.zmq.Socket.recv_multipart`.
Callbacks can also be registered for send events with {meth}`~.ZMQStream.on_send`.

### {class}`.ZMQStream`

{class}`.ZMQStream` objects let you register callbacks to handle messages as they arrive,
for use with the tornado eventloop.

#### {meth}`.ZMQStream.send`

ZMQStream objects do have {meth}`~.ZMQStream.send` and {meth}`~.ZMQStream.send_multipart`
methods, which behaves the same way as {meth}`.zmq.Socket.send`, but instead of sending right
away, the {class}`~.tornado.ioloop.IOLoop` will wait until socket is able to send (for instance if `HWM`
is met, or a `REQ/REP` pattern prohibits sending at a certain point). Messages sent via
send will also be passed to the callback registered with {meth}`~.ZMQStream.on_send` after
sending.

#### {meth}`~.ZMQStream.on_recv`

{meth}`.ZMQStream.on_recv` is the primary method for using a ZMQStream. It registers a
callback to fire with messages as they are received, which will *always* be multipart,
even if its length is 1. You can easily use this to build things like an echo socket:

```python
s = ctx.socket(zmq.REP)
s.bind("tcp://localhost:12345")
stream = ZMQStream(s)


def echo(msg):
    stream.send_multipart(msg)


stream.on_recv(echo)
ioloop.IOLoop.instance().start()
```

on_recv can also take a `copy` flag, just like {meth}`.zmq.Socket.recv`. If `copy=False`, then
callbacks registered with on_recv will receive tracked {class}`.Frame` objects instead of
bytes.

```{note}
A callback must be registered using either {meth}`.ZMQStream.on_recv` or
{meth}`.ZMQStream.on_recv_stream` before any data will be received on the
underlying socket.  This allows you to temporarily pause processing on a
socket by setting both callbacks to None.  Processing can later be resumed
by restoring either callback.
```

#### {meth}`~.ZMQStream.on_recv_stream`

{meth}`.ZMQStream.on_recv_stream` is just like on_recv above, but the callback will be
passed both the message and the stream, rather than just the message.  This is meant to make
it easier to use a single callback with multiple streams.

```python
s1 = ctx.socket(zmq.REP)
s1.bind("tcp://localhost:12345")
stream1 = ZMQStream(s1)

s2 = ctx.socket(zmq.REP)
s2.bind("tcp://localhost:54321")
stream2 = ZMQStream(s2)


def echo(stream, msg):
    stream.send_multipart(msg)


stream1.on_recv_stream(echo)
stream2.on_recv_stream(echo)

ioloop.IOLoop.instance().start()
```

#### {meth}`~.ZMQStream.flush`

Sometimes with an eventloop, there can be multiple events ready on a single iteration of
the loop. The {meth}`.ZMQStream.flush` method allows developers to pull messages off of
the queue to enforce some priority over the event loop ordering. flush pulls any pending
events off of the queue. You can specify to flush only recv events, only send events, or
any events, and you can specify a limit for how many events to flush in order to prevent
starvation.

(zmq-green)=

## PyZMQ and gevent

PyZMQ ≥ 2.2.0.1 ships with a [gevent](https://www.gevent.org/) compatible API as {mod}`zmq.green`.
To use it, simply:

```python
import zmq.green as zmq
```

Then write your code as normal.

Socket.send/recv and zmq.Poller are gevent-aware.

In PyZMQ ≥ 2.2.0.2, green.device and green.eventloop should be gevent-friendly as well.

```{note}
The green device does *not* release the GIL, unlike the true device in zmq.core.
```

zmq.green.eventloop includes minimally patched IOLoop/ZMQStream in order to use the gevent-enabled Poller,
so you should be able to use the ZMQStream interface in gevent apps as well,
though using two eventloops simultaneously (tornado + gevent) is not recommended.

```{warning}
There is a [known issue](https://github.com/zeromq/pyzmq/issues/229) in gevent ≤ 1.0 or libevent,
which can cause zeromq socket events to be missed.
PyZMQ works around this by adding a timeout so it will not wait forever for gevent to notice events.
The only known solution for this is to use gevent ≥ 1.0, which is currently at 1.0b3,
and does not exhibit this behavior.
```

```{seealso}
zmq.green examples [on GitHub](https://github.com/zeromq/pyzmq/tree/HEAD/examples/gevent).
```

{mod}`zmq.green` began as [gevent_zeromq](https://github.com/tmc/gevent-zeromq),
merged into the pyzmq project.

[tornado]: https://www.tornadoweb.org
