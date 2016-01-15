.. PyZMQ eventloop doc, by Min Ragan-Kelley, 2011

.. _eventloop:

====================
Eventloops and PyZMQ
====================

Integrating zmq with eventloops is *almost* really easy,
since most eventloops happily support sockets.
What gets messy is that zmq sockets aren't regular sockets,
so they need special handling.
libzmq provides a :func:`zmq_poll` function that is the same as regular polling,
but **also** support zmq sockets. PyZMQ wrapps this in a :class:`~.Poller` class.
Most of pyzmq's eventloop support involves setting up existing eventloops (tornado, asyncio)
to use :func:`zmq_poll` as the inner poller, rather than the default select/poll/etc.
Once that's done, zmq sockets can be happily treated like regular sockets,
and regular sockets should continue to work as before.

.. note::

    It *is* possible to integrate zmq sockets into existing eventloops without modifying the poller
    by using the ``socket.FD`` attribute.
    The incredibly unfortunate aspect of this is that it was implemented as an edge-triggered fd,
    which is highly error prone, and I wouldn't recommend using unless absolutely necessary.
    This is used in :mod:`zmq.green`, and has been the source of many problems.


Tornado IOLoop
==============

Facebook's `Tornado`_ includes an eventloop for handing poll events on filedescriptors and
native sockets. We have included a small part of Tornado (specifically its
:mod:`.ioloop`), and adapted its :class:`IOStream` class into :class:`.ZMQStream` for
handling poll events on ØMQ sockets. A ZMQStream object works much like a Socket object,
but instead of calling :meth:`~.Socket.recv` directly, you register a callback with
:meth:`~.ZMQStream.on_recv`. Callbacks can also be registered for send events
with :meth:`~.ZMQStream.on_send`.


:func:`install()`
-----------------

With PyZMQ's ioloop, you can use zmq sockets in any tornado application.  You can tell tornado to use zmq's poller by calling the :func:`.ioloop.install` function:

.. sourcecode:: python

    from zmq.eventloop import ioloop
    ioloop.install()

You can also do the same thing by requesting the global instance from pyzmq:

.. sourcecode:: python

    from zmq.eventloop.ioloop import IOLoop
    loop = IOLoop.current()

This configures tornado's :class:`tornado.ioloop.IOLoop` to use zmq's poller,
and registers the current instance.

Either ``install()`` or retrieving the zmq instance must be done before the global * instance is registered, else there will be a conflict.

It is possible to use PyZMQ sockets with tornado *without* registering as the global instance,
but it is less convenient. First, you must instruct the tornado IOLoop to use the zmq poller:

.. sourcecode:: python

    from zmq.eventloop.ioloop import ZMQIOLoop

    loop = ZMQIOLoop()

Then, when you instantiate tornado and ZMQStream objects, you must pass the `io_loop`
argument to ensure that they use this loop, instead of the global instance.

This is especially useful for writing tests, such as this:

.. sourcecode:: python

    from tornado.testing import AsyncTestCase
    from zmq.eventloop.ioloop import ZMQIOLoop
    from zmq.eventloop.zmqstream import ZMQStream

    class TestZMQBridge(AsyncTestCase):

         # Use a ZMQ-compatible I/O loop so that we can use `ZMQStream`.
         def get_new_ioloop(self):
             return ZMQIOLoop()

You can also manually install this IOLoop as the global tornado instance, with:

.. sourcecode:: python

    from zmq.eventloop.ioloop import ZMQIOLoop
    loop = ZMQIOLoop()
    loop.install()

.. _futures:

Futures and coroutines
----------------------

PyZMQ 15 adds :mod:`zmq.eventloop.future`, containing a Socket subclass
that returns :class:`~.tornado.concurrent.Future` objects for use in :mod:`tornado` coroutines.


:class:`ZMQStream`
------------------

:class:`ZMQStream` objects let you register callbacks to handle messages as they arrive,
for use with the tornado eventloop.

:meth:`send`
************

ZMQStream objects do have :meth:`~.ZMQStream.send` and :meth:`~.ZMQStream.send_multipart`
methods, which behaves the same way as :meth:`.Socket.send`, but instead of sending right
away, the :class:`.IOLoop` will wait until socket is able to send (for instance if ``HWM``
is met, or a ``REQ/REP`` pattern prohibits sending at a certain point). Messages sent via
send will also be passed to the callback registered with :meth:`~.ZMQStream.on_send` after
sending.

:meth:`on_recv`
***************

:meth:`.ZMQStream.on_recv` is the primary method for using a ZMQStream. It registers a
callback to fire with messages as they are received, which will *always* be multipart,
even if its length is 1. You can easily use this to build things like an echo socket:

.. sourcecode:: python

    s = ctx.socket(zmq.REP)
    s.bind('tcp://localhost:12345')
    stream = ZMQStream(s)
    def echo(msg):
        stream.send_multipart(msg)
    stream.on_recv(echo)
    ioloop.IOLoop.instance().start()

on_recv can also take a `copy` flag, just like :meth:`.Socket.recv`. If `copy=False`, then
callbacks registered with on_recv will receive tracked :class:`.Frame` objects instead of
bytes.

.. note::

    A callback must be registered using either :meth:`.ZMQStream.on_recv` or
    :meth:`.ZMQStream.on_recv_stream` before any data will be received on the
    underlying socket.  This allows you to temporarily pause processing on a
    socket by setting both callbacks to None.  Processing can later be resumed
    by restoring either callback.


:meth:`on_recv_stream`
**********************

:meth:`.ZMQStream.on_recv_stream` is just like on_recv above, but the callback will be
passed both the message and the stream, rather than just the message.  This is meant to make
it easier to use a single callback with multiple streams.

.. sourcecode:: python

    s1 = ctx.socket(zmq.REP)
    s1.bind('tcp://localhost:12345')
    stream1 = ZMQStream(s1)

    s2 = ctx.socket(zmq.REP)
    s2.bind('tcp://localhost:54321')
    stream2 = ZMQStream(s2)

    def echo(stream, msg):
        stream.send_multipart(msg)

    stream1.on_recv_stream(echo)
    stream2.on_recv_stream(echo)

    ioloop.IOLoop.instance().start()


:meth:`flush`
*************

Sometimes with an eventloop, there can be multiple events ready on a single iteration of
the loop. The :meth:`~.ZMQStream.flush` method allows developers to pull messages off of
the queue to enforce some priority over the event loop ordering. flush pulls any pending
events off of the queue. You can specify to flush only recv events, only send events, or
any events, and you can specify a limit for how many events to flush in order to prevent
starvation.

.. _Tornado: https://github.com/facebook/tornado

.. _asyncio:

AsyncIO
=======

PyZMQ 15 adds support for :mod:`asyncio` via :mod:`zmq.asyncio`.

.. _zmq_green:

PyZMQ and gevent
================

PyZMQ ≥ 2.2.0.1 ships with a `gevent <http://www.gevent.org/>`_ compatible API as :mod:`zmq.green`.
To use it, simply:

.. sourcecode:: python

    import zmq.green as zmq

Then write your code as normal.

Socket.send/recv and zmq.Poller are gevent-aware.

In PyZMQ ≥ 2.2.0.2, green.device and green.eventloop should be gevent-friendly as well.

.. note::

    The green device does *not* release the GIL, unlike the true device in zmq.core.

zmq.green.eventloop includes minimally patched IOLoop/ZMQStream in order to use the gevent-enabled Poller,
so you should be able to use the ZMQStream interface in gevent apps as well,
though using two eventloops simultaneously (tornado + gevent) is not recommended.

.. warning::

    There is a `known issue <https://github.com/zeromq/pyzmq/issues/229>`_ in gevent ≤ 1.0 or libevent,
    which can cause zeromq socket events to be missed.
    PyZMQ works around this by adding a timeout so it will not wait forever for gevent to notice events.
    The only known solution for this is to use gevent ≥ 1.0, which is currently at 1.0b3,
    and does not exhibit this behavior.

.. seealso::

    zmq.green examples `on GitHub <https://github.com/zeromq/pyzmq/tree/master/examples/gevent>`_.

:mod:`zmq.green` is simply `gevent_zeromq <https://github.com/traviscline/gevent_zeromq>`_,
merged into the pyzmq project.

