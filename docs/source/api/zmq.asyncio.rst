.. AUTO-GENERATED FILE -- DO NOT EDIT!

asyncio
=======

Module: :mod:`zmq.asyncio`
--------------------------
.. automodule:: zmq.asyncio

.. currentmodule:: zmq.asyncio

.. versionadded:: 15.0

As of 15.0, pyzmq now supports :mod:`asyncio`, via :mod:`zmq.asyncio`.
When imported from this module, blocking methods such as
:meth:`zmq.asyncio.Socket.recv_multipart`, :meth:`zmq.asyncio.Socket.poll`,
and :meth:`zmq.asyncio.Poller.poll` return :class:`~.asyncio.Future` s.

It also provides a :class:`zmq.asyncio.ZMQEventLoop`.

.. sourcecode:: python

    import asyncio
    import zmq
    import zmq.asyncio

    ctx = zmq.asyncio.Context()
    loop = zmq.asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)

    @asyncio.coroutine
    def recv_and_process():
        sock = ctx.socket(zmq.PULL)
        sock.bind(url)
        msg = yield from sock.recv_multipart() # waits for msg to be ready
        reply = yield from async_process(msg)
        yield from sock.send_multipart(reply)

    loop.run_until_complete(recv_and_process())


Classes
-------

:class:`ZMQEventLoop`
~~~~~~~~~~~~~~~~~~~~~

An asyncio event loop using zmq_poll for zmq socket support.

.. autoclass:: ZMQEventLoop


:class:`Context`
~~~~~~~~~~~~~~~~

Context class that creates Future-returning sockets. See :class:`zmq.Context` for more info.

.. autoclass:: Context
  :noindex:



:class:`Socket`
~~~~~~~~~~~~~~~

Socket subclass that returns :class:`asyncio.Future` s from blocking methods,
for use in coroutines and async applications.

.. seealso::

    :class:`zmq.Socket` for the inherited API.

.. autoclass:: Socket
  :noindex:

  .. automethod:: recv
    :noindex:
  .. automethod:: recv_multipart
    :noindex:
  .. automethod:: send
    :noindex:
  .. automethod:: send_multipart
    :noindex:
  .. automethod:: poll
    :noindex:

:class:`Poller`
~~~~~~~~~~~~~~~

Poller subclass that returns :class:`asyncio.Future` s from poll,
for use in coroutines and async applications.

.. seealso::

    :class:`zmq.Poller` for the inherited API.

.. autoclass:: Poller
  :noindex:

  .. automethod:: poll
    :noindex:
