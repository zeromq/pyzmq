.. PyZMQ Bindings doc, by Min Ragan-Kelley, 2011

.. _bindings:

More Than Just Bindings
=======================

PyZMQ is ostensibly the Python bindings for `ØMQ`_, but the project, following
Python's 'batteries included' philosophy, provides more than just Python methods and
objects for calling into the ØMQ C++ library.


The Core as Bindings
--------------------

PyZMQ is currently broken up into four subpackages. First, is the Core. :mod:`zmq.core`
contains the actual bindings for ZeroMQ, and no extended functionality beyond the very
basic. The core modules are split, such that each basic ZeroMQ object (or function, if no
object is associated) is a separate module, e.g. :mod:`zmq.core.context` contains the
:class:`.Context` object, :mod:`zmq.core.poll` contains a :class:`.Poller` object, as well
as the :func:`.select` function, etc. ZMQ constants are, for convenience, all kept
together in :mod:`zmq.core.constants`.

There are two reasons for breaking the core into submodules: *recompilation* and
*derivative projects*. The monolithic PyZMQ became quite tedious to have to recompile
everything for a small change to a single object. With separate files, that's no longer
necessary. The second reason has to do with Cython. PyZMQ is written in Cython, a tool for
efficiently writing C-extensions for Python. By separating out our objects into individual
`pyx` files, each with their declarations in a `pxd` header, other projects can write
extensions in Cython and call directly to ZeroMQ at the C-level without the penalty of
going through our Python objects.


Core Extensions
---------------

We have extended the core functionality in two ways that appear inside the :mod:`core`
bindings, and are not general ØMQ features.

Builtin Serialization
*********************

First, we added common serialization with the builtin :py:mod:`json` and :py:mod:`pickle`
as first-class methods to the :class:`Socket` class. A socket has the methods
:meth:`~.Socket.send_json` and :meth:`~.Socket.send_pyobj`, which correspond to sending an
object over the wire after serializing with :mod:`json` and :mod:`pickle` respectively,
and any object sent via those methods can be reconstructed with the
:meth:`~.Socket.recv_json` and :meth:`~.Socket.recv_pyobj` methods. Unicode strings are
other objects that are not unambiguously sendable over the wire, so we include
:meth:`~.Socket.send_unicode` and :meth:`~.Socket.recv_unicode` that simply send via the
unambiguous utf-8 byte encoding. See :ref:`our Unicode discussion <unicode>` for more
information on the trials and tribulations of working with Unicode in a C extension while
supporting Python 2 and 3.

MessageTracker
**************

The second extension of basic ØMQ functionality is the :class:`MessageTracker`. The
MessageTracker is an object used to track when the underlying ZeroMQ is done with a
message buffer. One of the main use cases for ØMQ in Python is the ability to perform
non-copying sends. Thanks to Python's buffer interface, many objects (including NumPy
arrays) provide the buffer interface, and are thus directly sendable. However, as with any
asynchronous non-copying messaging system like ØMQ or MPI, it can be important to know
when the message has actually been sent, so it is safe again to edit the buffer without
worry of corrupting the message. This is what the MessageTracker is for.

The MessageTracker is a simple object, but there is a penalty to its use. Since by its
very nature, the MessageTracker must involve threadsafe communication (specifically a
builtin :py:class:`~Queue.Queue` object), instantiating a MessageTracker takes a modest
amount of time (10s of µs), so in situations instantiating many small messages, this can
actually dominate performance. As a result, tracking is optional, via the ``track`` flag,
which is optionally passed, always defaulting to ``False``, in each of the three places
where a Message is instantiated: The :class:`.Message` constructor, and non-copying sends
and receives.

A MessageTracker is very simple, and has just one method and one attribute. The property
:attr:`MessageTracker.done` will be ``True`` when the Message(s) being tracked are no
longer in use by ØMQ, and :meth:`.MessageTracker.wait` will block, waiting for the
Message(s) to be released.

.. Note::

    A message cannot be tracked after it has been instantiated without tracking. If a
    Message is to even have the *option* of tracking, it must be constructed with
    ``track=True``.


Extensions
----------

So far, PyZMQ includes three extensions to core ØMQ that we found basic enough to be
included in PyZMQ itself:

* :ref:`zmq.log <logging>` : Logging handlers for hooking Python logging up to the
  network
* :ref:`zmq.devices <devices>` : Custom devices and objects for running devices in the 
  background
* :ref:`zmq.eventloop <eventloop>` : The `Tornado`_ event loop, adapted for use 
  with ØMQ sockets.

.. _ØMQ: http://www.zeromq.org
.. _Tornado: https://github.com/facebook/tornado