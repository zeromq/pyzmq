.. AUTO-GENERATED FILE -- DO NOT EDIT!

eventloop.future
================

Module: :mod:`eventloop.future`
-------------------------------
.. automodule:: zmq.eventloop.future

.. currentmodule:: zmq.eventloop.future

.. versionadded:: 15.0

As of pyzmq 15, there is a new Socket subclass that returns Futures for recv methods,
which can be found at :class:`zmq.eventloop.future.Socket`.
You can create these sockets by instantiating a :class:`~zmq.eventloop.future.Context`
from the same module.
These sockets let you easily use zmq with tornado's coroutines.

.. seealso::

    :mod:`tornado:tornado.gen`

.. sourcecode:: python

    from tornado import gen
    from zmq.eventloop.future import Context
    
    ctx = Context()
    
    @gen.coroutine
    def recv_and_process():
        sock = ctx.socket(zmq.PULL)
        sock.bind(url)
        msg = yield sock.recv_multipart() # waits for msg to be ready
        reply = yield async_process(msg)
        yield sock.send_multipart(reply)

Classes
-------

:class:`Context`
~~~~~~~~~~~~~~~~

Context class that creates Future-returning sockets. See :class:`zmq.Context` for more info.

.. autoclass:: Context
  :noindex:


:class:`Socket`
~~~~~~~~~~~~~~~

Socket subclass that returns :class:`~tornado.concurrent.Future` s from blocking methods,
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

Poller subclass that returns :class:`~tornado.concurrent.Future` s from poll,
for use in coroutines and async applications.

.. seealso::

    :class:`zmq.Poller` for the inherited API.

.. autoclass:: Poller
  :noindex:
  
  .. automethod:: poll
      :noindex:
