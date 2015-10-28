.. AUTO-GENERATED FILE -- DO NOT EDIT!

eventloop.future
================

Module: :mod:`eventloop.future`
-------------------------------
.. automodule:: zmq.eventloop.future

.. currentmodule:: zmq.eventloop.future

Classes
-------

:class:`Context`
~~~~~~~~~~~~~~~~

Context class that creates Future-returning sockets. See :class:`zmq.Context` for more info.

.. autoclass:: Context



:class:`Socket`
~~~~~~~~~~~~~~~

Socket subclass that returns :class:`Future`s from recv methods,
for use in coroutines, async applications.

.. autoclass:: Socket
  
  .. automethod:: recv
  .. automethod:: recv_multipart
