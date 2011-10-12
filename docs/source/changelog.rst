.. PyZMQ changelog summary, started by Min Ragan-Kelley, 2011

.. _changelog:

================
Changes in PyZMQ
================

This is a coarse summary of changes in pyzmq versions.  For a real changelog, consult the
`git log <https://github.com/zeromq/pyzmq/commits>`_

2.1.10
======

* Add support for libzmq-3.0 LABEL prefixes:

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

