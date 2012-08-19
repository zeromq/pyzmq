.. PyZMQ changelog summary, started by Min Ragan-Kelley, 2011

.. _changelog:

================
Changes in PyZMQ
================

This is a coarse summary of changes in pyzmq versions.  For a real changelog, consult the
`git log <https://github.com/zeromq/pyzmq/commits>`_

2.2.0.1
=======

This is a tech-preview release, to try out some new features.
It is expected to be short-lived, as there are likely to be issues to iron out,
particularly with the new pip-install support.

Experimental New Stuff
----------------------

These features are marked 'experimental', which means that their APIs are not set in stone,
and may be removed or changed in incompatible ways in later releases.


Threadsafe ZMQStream
********************

With the IOLoop inherited from tornado, there is exactly one method that is threadsafe:
:meth:`.IOLoop.add_callback`.  With this release, we are trying an experimental option
to pass all IOLoop calls via this method, so that ZMQStreams can be used from one thread
while the IOLoop runs in another.  To try out a threadsafe stream:

.. sourcecode:: python

    stream = ZMQStream(socket, threadsafe=True)


pip install pyzmq
*****************

PyZMQ should now be pip installable, even on systems without libzmq.
In these cases, when pyzmq fails to find an appropriate libzmq to link against,
it will try to build libzmq as a Python extension.
This work is derived from `pyzmq_static <https://github.com/brandon-rhodes/pyzmq-static>`_.

To this end, PyZMQ source distributions include the sources for libzmq (2.2.0) and libuuid (2.21),
both used under the LGPL.


zmq.green
*********

The excellent `gevent_zeromq <https://github.com/traviscline/gevent_zeromq>`_ socket
subclass which provides `gevent <http://www.gevent.org/>`_ compatibility has been merged as
:mod:`zmq.green`.

.. seealso::

    :ref:`zmq_green`


Bugs fixed
----------

* TIMEO sockopts are properly included for libzmq-2.2.0
* avoid garbage collection of sockets after fork (would cause ``assert (mailbox.cpp:79)``).


2.2.0
=====

Some effort has gone into refining the pyzmq API in this release to make it a model for 
other language bindings.  This is principally made in a few renames of objects and methods,
all of which leave the old name for backwards compatibility.

.. note::

    As of this release, all code outside ``zmq.core`` is BSD licensed (where
    possible), to allow more permissive use of less-critical code and utilities.

Name Changes
------------

* The :class:`~.Message` class has been renamed to :class:`~.Frame`, to better match other
  zmq bindings. The old Message name remains for backwards-compatibility.  Wherever pyzmq
  docs say "Message", they should refer to a complete zmq atom of communication (one or
  more Frames, connected by ZMQ_SNDMORE). Please report any remaining instances of
  Message==MessagePart with an Issue (or better yet a Pull Request).

* All ``foo_unicode`` methods are now called ``foo_string`` (``_unicode`` remains for
  backwards compatibility).  This is not only for cross-language consistency, but it makes
  more sense in Python 3, where native strings are unicode, and the ``_unicode`` suffix
  was wedded too much to Python 2.

Other Changes and Removals
--------------------------

* ``prefix`` removed as an unused keyword argument from :meth:`~.Socket.send_multipart`.

* ZMQStream :meth:`~.ZMQStream.send` default has been changed to `copy=True`, so it matches
  Socket :meth:`~.Socket.send`.

* ZMQStream :meth:`~.ZMQStream.on_err` is deprecated, because it never did anything.

* Python 2.5 compatibility has been dropped, and some code has been cleaned up to reflect
  no-longer-needed hacks.

* Some Cython files in :mod:`zmq.core` have been split, to reduce the amount of 
  Cython-compiled code.  Much of the body of these files were pure Python, and thus did
  not benefit from the increased compile time.  This change also aims to ease maintaining
  feature parity in other projects, such as 
  `pyzmq-ctypes <https://github.com/svpcom/pyzmq-ctypes>`_.


New Stuff
---------

* :class:`~.Context` objects can now set default options when they create a socket. These
  are set and accessed as attributes to the context.  Socket options that do not apply to a
  socket (e.g. SUBSCRIBE on non-SUB sockets) will simply be ignored.

* :meth:`~.ZMQStream.on_recv_stream` has been added, which adds the stream itself as a
  second argument to the callback, making it easier to use a single callback on multiple
  streams.

* A :attr:`~Frame.more` boolean attribute has been added to the :class:`~.Frame` (née
  Message) class, so that frames can be identified as terminal without extra queires of
  :attr:`~.Socket.rcvmore`.


Experimental New Stuff
----------------------

These features are marked 'experimental', which means that their APIs are not
set in stone, and may be removed or changed in incompatible ways in later releases.

* :mod:`zmq.web` added for load-balancing requests in a tornado webapp with zeromq.


2.1.11
======

* remove support for LABEL prefixes.  A major feature of libzmq-3.0, the LABEL
  prefix, has been removed from libzmq, prior to the first stable libzmq 3.x release.
  
  * The prefix argument to :meth:`~.Socket.send_multipart` remains, but it continue to behave in
    exactly the same way as it always has on 2.1.x, simply prepending message parts.
  
  * :meth:`~.Socket.recv_multipart` will always return a list, because prefixes are once
    again indistinguishable from regular message parts.

* add :meth:`.Socket.poll` method, for simple polling of events on a single socket.

* no longer require monkeypatching tornado IOLoop.  The :class:`.ioloop.ZMQPoller` class
  is a poller implementation that matches tornado's expectations, and pyzmq sockets can
  be used with any tornado application just by specifying the use of this poller.  The
  pyzmq IOLoop implementation now only trivially differs from tornado's.

  It is still recommended to use :func:`.ioloop.install`, which sets *both* the zmq and
  tornado global IOLoop instances to the same object, but it is no longer necessary.

  .. warning::

    The most important part of this change is that the ``IOLoop.READ/WRITE/ERROR``
    constants now match tornado's, rather than being mapped directly to the zmq
    ``POLLIN/OUT/ERR``. So applications that used the low-level :meth:`IOLoop.add_handler`
    code with ``POLLIN/OUT/ERR`` directly (used to work, but was incorrect), rather than
    using the IOLoop class constants will no longer work. Fixing these to use the IOLoop
    constants should be insensitive to the actual value of the constants.

2.1.10
======

* Add support for libzmq-3.0 LABEL prefixes:

  .. warning::

    This feature has been removed from libzmq, and thus removed from future pyzmq
    as well.

  * send a message with label-prefix with:

    .. sourcecode:: python

      send_multipart([b'msg', b'parts'], prefix=[b'label', b'prefix'])

  * :meth:`recv_multipart` returns a tuple of ``(prefix,msg)`` if a label prefix is detected
  * ZMQStreams and devices also respect the LABEL prefix

* add czmq-style close&term as :meth:`ctx.destroy`, so that :meth:`ctx.term`
  remains threadsafe and 1:1 with libzmq.
* :meth:`Socket.close` takes optional linger option, for setting linger prior
  to closing.
* add :func:`~zmq.core.version.zmq_version_info` and
  :func:`~zmq.core.version.pyzmq_version_info` for getting libzmq and pyzmq versions as
  tuples of numbers. This helps with the fact that version string comparison breaks down
  once versions get into double-digits.
* ioloop changes merged from upstream `Tornado <http://www.tornadoweb.org>`_ 2.1

2.1.9
=====

* added zmq.ssh tools for tunneling socket connections, copied from IPython
* Expanded sockopt support to cover changes in libzmq-4.0 dev.
* Fixed an issue that prevented :exc:`KeyboardInterrupts` from being catchable.
* Added attribute-access for set/getsockopt.  Setting/Getting attributes of :class:`Sockets`
  with the names of socket options is mapped to calls of set/getsockopt.

.. sourcecode:: python

    s.hwm = 10
    s.identity = b'whoda'
    s.linger
    # -1
    
* Terminating a :class:`~Context` closes the sockets it created, matching the behavior in
  `czmq <http://czmq.zeromq.org/>`_.
* :class:`ThreadDevices` use :meth:`Context.instance` to create sockets, so they can use
  inproc connections to sockets in other threads.
* fixed units error on :func:`zmq.select`, where the poll timeout was 1000 times longer
  than expected.
* Add missing ``DEALER/ROUTER`` socket type names (currently aliases, to be replacements for ``XREP/XREQ``).
* base libzmq dependency raised to 2.1.4 (first stable release) from 2.1.0.


2.1.7.1
=======

* bdist for 64b Windows only.  This fixed a type mismatch on the ``ZMQ_FD`` sockopt
  that only affected that platform.


2.1.7
=====

* Added experimental support for libzmq-3.0 API
* Add :func:`zmq.eventloop.ioloop.install` for using pyzmq's IOLoop in a tornado
  application.


2.1.4
=====

* First version with binary distribution support
* Added :meth:`~Context.instance()` method for using a single Context throughout an application
  without passing references around.

