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

.. autofunction:: zmq.curve_keypair

.. autofunction:: zmq.get_includes

.. autofunction:: zmq.get_library_dirs
