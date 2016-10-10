.. PyZMQ changelog summary, started by Min Ragan-Kelley, 2011

.. _changelog:

================
Changes in PyZMQ
================

This is a coarse summary of changes in pyzmq versions.
For a full changelog, consult the `git log <https://github.com/zeromq/pyzmq/commits>`_.


16.0
====

- Support for Python 2.6 and Python 3.2 is dropped. For old Pythons, use :command:`pip install "pyzmq<16"` to get the last version of pyzmq that supports these versions.
- Include zmq.h
- Deprecate ``zmq.Stopwatch``. Native Python timing tools can be used instead.
- Better support for using pyzmq as a Cython library
  - bundle zmq.h when pyzmq bundles libzmq as an extension
  - add :func:`zmq.get_library_dirs` to find bundled libzmq
- Updates to setup.py for Cython 0.25 compatibility
- Various asyncio/future fixes:
  - support raw sockets in pollers
  - allow cancelling async sends
- Fix :meth:`IOLoop.current` in :mod:`zmq.green`


15.4
====

- Load bundled libzmq extension with import rather than CDLL,
  which should fix some manifest issues in certain cases on Windows.
- Avoid installing asyncio sources on Python 2, which confuses some tools that run `python -m compileall`, which reports errors on the Python 3-only files.
- Bundle msvcp.dll in Windows wheels on CPython 3.5,
  which should fix wheel compatibility systems without Visual C++ 2015 redistributable.
- :meth:`zmq.Context.instance` is now threadsafe.
- FIX: sync some behavior in zmq_poll and setting LINGER on close/destroy with the CFFI backend.
- PERF: resolve send/recv immediately if events are available in async Sockets
- Async Sockets (asyncio, tornado) now support ``send_json``, ``send_pyobj``, etc.
- add preliminary support for ``zmq.DRAFT_API`` reflecting ZMQ_BUILD_DRAFT_API,
  which indicates whether new APIs in prereleases are available.


15.3
====

- Bump bundled libzmq to 4.1.5, using tweetnacl for bundled curve support instead of libsodium
- FIX: include .pxi includes in installation for consumers of Cython API
- FIX: various fixes in new async sockets
- Introduce :mod:`zmq.decorators` API for decorating functions to create sockets or contexts
- Add :meth:`zmq.Socket.subscribe` and :meth:`zmq.Socket.unsubscribe` methods to sockets, so that assignment is no longer needed for subscribing. Verbs should be methods!
  Assignment is still supported for backward-compatibility.
- Accept text (unicode) input to z85 encoding, not just bytes
- :meth:`zmq.Context.socket` forwards keyword arguments to the :class:`Socket` constructor

15.2
====

- FIX: handle multiple events in a single register call in :mod:`zmq.asyncio`
- FIX: unicode/bytes bug in password prompt in :mod:`zmq.ssh` on Python 3
- FIX: workaround gevent monkeypatches in garbage collection thread
- update bundled minitornado from tornado-4.3.
- improved inspection by setting ``binding=True`` in cython compile options
- add asyncio Authenticator implementation in :mod:`zmq.auth.asyncio`
- workaround overflow bug in libzmq preventing receiving messages larger than ``MAX_INT``

15.1
====

- FIX: Remove inadvertant tornado dependency when using :mod:`zmq.asyncio`
- FIX: 15.0 Python 3.5 wheels didn't work on Windows
- Add GSSAPI support to Authenticators
- Support new constants defined in upcoming libzmq-4.2.dev

15.0
====

PyZMQ 15 adds Future-returning sockets and pollers for both :mod:`asyncio` and :mod:`tornado`.

- add :mod:`asyncio` support via :mod:`zmq.asyncio`
- add :mod:`tornado` future support via :mod:`zmq.eventloop.future`
- trigger bundled libzmq if system libzmq is found to be < 3.
  System libzmq 2 can be forced by explicitly requesting ``--zmq=/prefix/``.


14.7.0
======

Changes:

- Update bundled libzmq to 4.1.2.
- Following the `lead of Python 3.5 <https://www.python.org/dev/peps/pep-0475/>`_,
  interrupted system calls will be retried.

Fixes:

- Fixes for CFFI backend on Python 3 + support for PyPy 3.
- Verify types of all frames in :meth:`~zmq.Socket.send_multipart` before sending,
  to avoid partial messages.
- Fix build on Windows when both debug and release versions of libzmq are found.
- Windows build fixes for Python 3.5.

14.6.0
======

Changes:

- improvements in :meth:`zmq.Socket.bind_to_random_port`:
   - use system to allocate ports by default
   - catch EACCES on Windows
- include libsodium when building bundled libzmq on Windows (includes wheels on PyPI)
- pyzmq no longer bundles external libzmq when making a bdist.
  You can use `delocate <https://pypi.python.org/pypi/delocate>`_ to do this.

Bugfixes:

- add missing :attr:`ndim` on memoryviews of Frames
- allow :func:`copy.copy` and :func:`copy.deepcopy` on Sockets, Contexts


14.5.0
======

Changes:

- use pickle.DEFAULT_PROTOCOL by default in send_pickle
- with the release of pip-6, OS X wheels are only marked as 10.6-intel,
  indicating that they should be installable on any newer or single-arch Python.
- raise SSHException on failed check of host key

Bugfixes:

- fix method name in utils.wi32.allow_interrupt
- fork-related fixes in garbage collection thread
- add missing import in ``zmq.__init__``, causing failure to import in some circumstances


14.4.1
======

Bugfixes for 14.4

- SyntaxError on Python 2.6 in zmq.ssh
- Handle possible bug in garbage collection after fork


14.4.0
======

New features:

- Experimental support for libzmq-4.1.0 rc (new constants, plus :func:`zmq.has`).
- Update bundled libzmq to 4.0.5
- Update bundled libsodium to 1.0.0
- Fixes for SSH dialogs when using :mod:`zmq.ssh` to create tunnels
- More build/link/load fixes on OS X and Solaris
- Get Frame metadata via dict access (libzmq 4)
- Contexts and Sockets are context managers (term/close on ``__exit__``)
- Add :class:`zmq.utils.win32.allow_interrupt` context manager for catching SIGINT on Windows

Bugs fixed:

- Bundled libzmq should not trigger recompilation after install on PyPy

14.3.1
======

.. note::

    pyzmq-14.3.1 is the last version to include bdists for Python 3.3

Minor bugfixes to pyzmq 14.3:

- Fixes to building bundled libzmq on OS X < 10.9
- Fixes to import-failure warnings on Python 3.4
- Fixes to tests
- Pull upstream fixes to zmq.ssh for ssh multiplexing

14.3.0
======

- PyZMQ no longer calls :meth:`.Socket.close` or :meth:`.Context.term` during process cleanup.
  Changes to garbage collection in Python 3.4 make this impossible to do sensibly.
- :meth:`ZMQStream.close` closes its socket immediately, rather than scheduling a timeout.
- Raise the original ImportError when importing zmq fails.
  Should be more informative than `no module cffi...`.

.. warning::

    Users of Python 3.4 should not use pyzmq < 14.3, due to changes in garbage collection.


14.2.0
======

New Stuff
---------

- Raise new ZMQVersionError when a requested method is not supported by the linked libzmq.
  For backward compatibility, this subclasses NotImplementedError.


Bugs Fixed
----------

- Memory leak introduced in pyzmq-14.0 in zero copy.
- OverflowError on 32 bit systems in zero copy.


14.1.0
======

Security
--------

The headline features for 14.1 are adding better support for libzmq's
security features.

- When libzmq is bundled as a Python extension (e.g. wheels, eggs),
  libsodium is also bundled (excluding Windows),
  ensuring that libzmq security is available to users who install from wheels
- New :mod:`zmq.auth`, implementing zeromq's ZAP authentication,
  modeled on czmq zauth.
  For more information, see the `examples <https://github.com/zeromq/pyzmq/tree/master/examples/>`_.


Other New Stuff
---------------

- Add PYZMQ_BACKEND for enabling use of backends outside the pyzmq codebase.
- Add :attr:`~.Context.underlying` property and :meth:`~.Context.shadow`
  method to Context and Socket, for handing off sockets and contexts.
  between pyzmq and other bindings (mainly pyczmq_).
- Add TOS, ROUTER_HANDOVER, and IPC_FILTER constants from libzmq-4.1-dev.
- Add Context option support in the CFFI backend.
- Various small unicode and build fixes, as always.
- :meth:`~.Socket.send_json` and :meth:`~.Socket.recv_json` pass any extra kwargs to ``json.dumps/loads``.


.. _pyczmq: https://github.com/zeromq/pyczmq


Deprecations
------------

- ``Socket.socket_type`` is deprecated, in favor of ``Socket.type``,
  which has been available since 2.1.


14.0.1
======

Bugfix release

- Update bundled libzmq to current (4.0.3).
- Fix bug in :meth:`.Context.destroy` with no open sockets.
- Threadsafety fixes in the garbage collector.
- Python 3 fixes in :mod:`zmq.ssh`.


14.0.0
======

* Update bundled libzmq to current (4.0.1).
* Backends are now implemented in ``zmq.backend`` instead of ``zmq.core``.
  This has no effect on public APIs.
* Various build improvements for Cython and CFFI backends (PyPy compiles at build time).
* Various GIL-related performance improvements - the GIL is no longer touched from a zmq IO thread.
* Adding a constant should now be a bit easier - only zmq/sugar/constant_names should need updating,
  all other constant-related files should be automatically updated by ``setup.py constants``.
* add support for latest libzmq-4.0.1
  (includes ZMQ_CURVE security and socket event monitoring).

New stuff
---------

- :meth:`.Socket.monitor`
- :meth:`.Socket.get_monitor_socket`
- :func:`zmq.curve_keypair`
- :mod:`zmq.utils.monitor`
- :mod:`zmq.utils.z85`


13.1.0
======

The main new feature is improved tornado 3 compatibility.
PyZMQ ships a 'minitornado' submodule, which contains a small subset of tornado 3.0.1,
in order to get the IOLoop base class.  zmq.eventloop.ioloop.IOLoop is now a simple subclass,
and if the system tornado is ≥ 3.0, then the zmq IOLoop is a proper registered subclass
of the tornado one itself, and minitornado is entirely unused.

13.0.2
======

Bugfix release!

A few things were broken in 13.0.0, so this is a quick bugfix release.

* **FIXED** EAGAIN was unconditionally turned into KeyboardInterrupt
* **FIXED** we used totally deprecated ctypes_configure to generate constants in CFFI backend
* **FIXED** memory leak in CFFI backend for PyPy
* **FIXED** typo prevented IPC_PATH_MAX_LEN from ever being defined
* **FIXED** various build fixes - linking with librt, Cython compatibility, etc.

13.0.1
======

defunct bugfix. We do not speak of this...

13.0.0
======

PyZMQ now officially targets libzmq-3 (3.2.2),
0MQ ≥ 2.1.4 is still supported for the indefinite future, but 3.x is recommended.
PyZMQ has detached from libzmq versioning,
and will just follow its own regular versioning scheme from now on.
PyZMQ bdists will include whatever is the latest stable libzmq release (3.2.2 for pyzmq-13.0).

.. note::

    set/get methods are exposed via get/setattr on all Context, Socket, and Frame classes.
    This means that subclasses of these classes that require extra attributes
    **must declare these attributes at the class level**.

Experiments Removed
-------------------

* The Threadsafe ZMQStream experiment in 2.2.0.1 was deemed inappropriate and not useful,
  and has been removed.
* The :mod:`zmq.web` experiment has been removed,
  to be developed as a `standalone project <https://github.com/ellisonbg/zmqweb>`_.

New Stuff
---------

* Support for PyPy via CFFI backend (requires py, ctypes-configure, and cffi).
* Add support for new APIs in libzmq-3

  - :meth:`.Socket.disconnect`
  - :meth:`.Socket.unbind`
  - :meth:`.Context.set`
  - :meth:`.Context.get`
  - :meth:`.Frame.set`
  - :meth:`.Frame.get`
  - :func:`zmq.proxy`
  - :class:`zmq.devices.Proxy`
  - Exceptions for common zmq errnos: :class:`zmq.Again`, :class:`zmq.ContextTerminated`
    (subclass :class:`ZMQError`, so fully backward-compatible).
  

* Setting and getting :attr:`.Socket.hwm` sets or gets *both* SNDHWM/RCVHWM for libzmq-3.
* Implementation splits core Cython bindings from pure-Python subclasses
  with sugar methods (send/recv_multipart). This should facilitate
  non-Cython backends and PyPy support [spoiler: it did!].


Bugs Fixed
----------

* Unicode fixes in log and monitored queue
* MinGW, ppc, cross-compilation, and HP-UX build fixes
* :mod:`zmq.green` should be complete - devices and tornado eventloop both work
  in gevent contexts.


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


Bugs Fixed
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

