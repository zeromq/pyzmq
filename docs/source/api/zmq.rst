zmq
===

.. automodule:: zmq

.. currentmodule:: zmq

Basic Classes
-------------

:class:`Context`
****************


.. autoclass:: Context
  :members:
  :inherited-members:
  :exclude-members: sockopts, closed, __del__, __enter__, __exit__, __copy__, __deepcopy__, __delattr__, __getattr__, __setattr__,

  .. attribute:: closed

      boolean - whether the context has been terminated.
      If True, you can no longer use this Context.


:class:`Socket`
***************


.. autoclass:: Socket
  :members:
  :inherited-members:
  :exclude-members: closed, context, getsockopt_unicode, recv_unicode, setsockopt_unicode, send_unicode, __del__, __enter__, __exit__, __copy__, __deepcopy__, __delattr__, __getattr__, __setattr__,

  .. attribute:: closed

      boolean - whether the socket has been closed.
      If True, you can no longer use this Socket.

  .. attribute:: copy_threshold

      integer - size (in bytes) below which messages
      should always be copied.
      Zero-copy support has nontrivial overhead
      due to the need to coordinate garbage collection
      with the libzmq IO thread,
      so sending small messages (typically < 10s of kB)
      with ``copy=False`` is often more expensive
      than with ``copy=True``.
      The initial default value is 65536 (64kB),
      a reasonable default based on testing.

      Defaults to :const:`zmq.COPY_THRESHOLD` on socket construction.
      Setting :const:`zmq.COPY_THRESHOLD` will define the default
      value for any subsequently created sockets.

      .. versionadded:: 17


:class:`Frame`
**************


.. autoclass:: Frame
  :members:
  :inherited-members:


:class:`MessageTracker`
***********************


.. autoclass:: MessageTracker
  :members:
  :inherited-members:


Polling
-------

:class:`Poller`
***************

.. autoclass:: Poller
  :members:
  :inherited-members:


.. autofunction:: zmq.select

Constants
---------

All libzmq constants are available as top-level attributes
(``zmq.PUSH``, etc.),
as well as via enums (``zmq.SocketType.PUSH``, etc.).

.. versionchanged:: 23

    constants for unavailable socket types
    or draft features will always be defined in pyzmq,
    whether the features themselves are available or not.

.. versionadded:: 23

    Each category of zmq constant is now available as an IntEnum.

.. autoenum:: SocketType

.. autoenum:: SocketOption

.. autoenum:: Flag

.. autoenum:: PollEvent

.. autoenum:: ContextOption

.. autoenum:: MessageOption

.. autoenum:: Event

.. autoenum:: SecurityMechanism

.. autoenum:: DeviceType

.. autoenum:: Errno

Exceptions
----------

:class:`ZMQError`
*****************

.. autoclass:: ZMQError
  :members:
  :inherited-members:


:class:`ZMQVersionError`
************************

.. autoclass:: ZMQVersionError
  :members:
  :inherited-members:

:class:`Again`
**************


.. autoclass:: Again


:class:`ContextTerminated`
**************************


.. autoclass:: ContextTerminated


:class:`NotDone`
****************


.. autoclass:: NotDone


:class:`ZMQBindError`
*********************


.. autoclass:: ZMQBindError



Functions
---------

.. autofunction:: zmq.zmq_version

.. autofunction:: zmq.pyzmq_version

.. autofunction:: zmq.zmq_version_info

.. autofunction:: zmq.pyzmq_version_info

.. autofunction:: zmq.has

.. autofunction:: zmq.device

.. autofunction:: zmq.proxy

.. autofunction:: zmq.proxy_steerable

.. autofunction:: zmq.curve_public

.. autofunction:: zmq.curve_keypair

.. autofunction:: zmq.get_includes

.. autofunction:: zmq.get_library_dirs
