(changelog)=

# Changes in PyZMQ

This is a coarse summary of changes in pyzmq versions.
For a full changelog, consult the [git log](https://github.com/zeromq/pyzmq/commits).

## 26

pyzmq 26 is a small release, but with some big changes _hopefully_ nobody will notice.
The highlights are:

- The Cython backend has been rewritten using Cython 3's pure Python mode.
- The build system has been rewritten to use CMake via [scikit-build-core] instead of setuptools (setup.py is gone!).
- Bundled libzmq is updated to 4.3.5, which changes its license from LGPL to MPL.

This means:

1. Cython >=3.0 is now a build requirement (if omitted, source distributions _should_ still build from Cython-generated .c files without any Cython present)
1. pyzmq's Cython backend is a single extension module, which should improve install size, import time, compile time, etc.
1. pyzmq's Cython backend is now BSD-licensed, matching the rest of pyzmq.
1. The license of the libzmq library (included in pyzmq wheels) starting with 4.3.5 is now Mozilla Public License 2.0 (MPL-2.0).
1. when building pyzmq from source and it falls back on bundled libzmq, libzmq and libsodium are built as static libraries using their own build systems (CMake for libzmq, autotools for libsodium except on Windows where it uses msbuild)
   rather than bundling libzmq with tweetnacl as a Python Extension.

Since the new build system uses libzmq and libsodium's own build systems, evaluated at install time, building pyzmq with bundled libzmq from source should be much more likely to succeed on a variety of platforms than the previous method, where their build system was skipped and approximated as a Python extension.
But I would also be _very_ surprised if I didn't break anything in the process of replacing 14 years of setup.py from scratch, especially cases like cross-compiling.
Please [report](https://github.com/zeromq/pyzmq/issues/new) any issues you encounter building pyzmq.

See [build docs](building-pyzmq) for more info.

__Enhancements__:

- `repr(Frame)` now produces a nice repr, summarizing Frame contents (without getting too large),
  e.g. `<zmq.Frame(b'abcdefghijkl'...52B)>`

__Breaking changes__:

- `str(Frame)` no longer returns the whole frame contents interpreted as utf8-bytes.
  Instead, it returns the new summarized repr,
  which produces more logical results with `print`, etc.
  `bytes(Frame)` remains unchanged, and utf-8 text strings can still be produced with:
  `bytes(Frame).decode("utf8")`,
  which works in all versions of pyzmq and does the same thing.
- Stop building Python 3.7 wheels for manylinux1, which reached EOL in January, 2022. The new build system doesn't seem to be able to find cmake in that environment.

## 25

### 25.1.1

25.1.1 is the first stable release with Python 3.12 wheels.

Changes:

- Allow Cython 0.29.35 to build Python 3.12 wheels (no longer require Cython 3)

Bugs fixed:

- Fix builds on Solaris by including generated platform.hpp
- Cleanup futures in `Socket.poll()`  that are cancelled and never return
- Fix builds with `-j` when numpy is present in the build env

### 25.1.0

pyzmq 25.1 mostly changes some packaging details of pyzmq, including support for installation from source on Python 3.12 beta 1.

Enhancements:

- Include address in error message when bind/connect fail.

Packaging changes:

- Fix inclusion of some test files in source distributions.
- Add Cython as a build-time dependency in `build-system.requires` metadata, following current [recommendations][cython-build-requires] of the Cython maintainers.
  We still ship generated Cython sources in source distributions, so it is not a _strict_ dependency for packagers using `--no-build-isolation`, but pip will install Cython as part of building pyzmq from source.
  This makes it more likely that past pyzmq releases will install on future Python releases, which often require an update to Cython but not pyzmq itself.
  For Python 3.12, Cython >=3.0.0b3 is required.

### 25.0.2

- Fix handling of shadow sockets in ZMQStream when the original sockets have been closed. A regression in 25.0.0, seen with jupyter-client 7.

### 25.0.1

Tiny bugfix release that should only affect users of {class}`~.PUBHandler` or pyzmq repackagers.

- Fix handling of custom Message types in {class}`~.PUBHandler`
- Small lint fixes to satisfy changes in mypy
- License files have been renamed to more standard LICENSE.BSD, LICENSE.LESSER to appease some license auto-detect tools.

### 25.0.0

New:

- Added `socket_class` argument to {func}`zmq.Context.socket`
- Support shadowing sockets with socket objects,
  not just via address, e.g. `zmq.asyncio.Socket(other_socket)`.
  Shadowing an object preserves a reference to the original,
  unlike shadowing via address.
- in {mod}`zmq.auth`, CredentialsProvider callbacks may now be async.
- {class}`~.zmq.eventloop.zmqstream.ZMQStream` callbacks may now be async.
- Add {class}`zmq.ReconnectStop` draft constants.
- Add manylinux_2_28 wheels for x86_64 CPython 3.10, 3.11, and PyPy 3.9 (these are _in addition to_ not _instead of_ the manylinux_2014 wheels).

Fixed:

- When {class}`~.zmq.eventloop.zmqstream.ZMQStream` is given an async socket,
  it now warns and hooks up events correctly with the underlying socket, so the callback gets the received message,
  instead of sending the callback the incorrect arguments.
- Fixed toml parse error in `pyproject.toml`,
  when installing from source with very old pip.
- Removed expressed dependency on `py` when running with pypy,
  which hasn't been used in some time.

Deprecated:

- {class}`zmq.auth.ioloop.IOLoopAuthenticator` is deprecated in favor of {class}`zmq.auth.asyncio.AsyncioAuthenticator`
- As part of migrating toward modern pytest, {class}`zmq.tests.BaseZMQTestCase` is deprecated and should not be used outside pyzmq.
- `python setup.py test` is deprecated as a way to launch the tests.
  Just use `pytest`.

Removed:

- Bundled subset of tornado's IOLoop (deprecated since pyzmq 17) is removed,
  so ZMQStream cannot be used without an actual install of tornado.
- Remove support for tornado 4,
  meaning tornado is always assumed to run on asyncio.

## 24

### 24.0.1

- Fix several possible resource warnings and deprecation warnings
  when cleaning up contexts and sockets,
  especially in pyzmq's own tests and when implicit teardown of objects is happening during process teardown.

### 24.0.0

pyzmq 24 has two breaking changes (one only on Windows), though they are not likely to affect most users.

Breaking changes:

- Due to a libzmq bug causing unavoidable crashes for some users,
  Windows wheels no longer bundle libzmq with AF_UNIX support.
  In order to enable AF_UNIX on Windows, pyzmq must be built from source,
  linking an appropriate build of libzmq (e.g. `libzmq-v142`).
  AF_UNIX support will be re-enabled in pyzmq wheels
  when libzmq published fixed releases.

- Using a {class}`zmq.Context` as a context manager or deleting a context without closing it now calls {meth}`zmq.Context.destroy` at exit instead of {meth}`zmq.Context.term`.
  This will have little effect on most users,
  but changes what happens when user bugs result in a context being _implicitly_ destroyed while sockets are left open.
  In almost all cases, this will turn what used to be a hang into a warning.
  However, there may be some cases where sockets are actively used in threads,
  which could result in a crash.
  To use sockets across threads, it is critical to properly and explicitly close your contexts and sockets,
  which will always avoid this issue.

## 23.2.1

Improvements:

- First release with wheels for Python 3.11 (thanks cibuildwheel!).
- linux aarch64 wheels now bundle the same libzmq (4.3.4) as all other builds,
  thanks to switching to native arm builds on CircleCI.

Fixes:

- Some type annotation fixes in devices.

## 23.2.0

Improvements:

- Use `zmq.Event` enums in `parse_monitor_message` for nicer reprs

Fixes:

- Fix building bundled libzmq with `ZMQ_DRAFT_API=1`
- Fix subclassing `zmq.Context` with additional arguments in the constructor.
  Subclasses may now have full control over the signature,
  rather than purely adding keyword-only arguments
- Typos and other small fixes

## 23.1.0

Fixing some regressions in 23.0:

- Fix global name of `zmq.EVENT_HANDSHAKE_*` constants
- Fix constants missing when using `import zmq.green as zmq`

Compatibility fixes:

- {func}`zmq.utils.monitor.recv_monitor_msg` now supports async Sockets.
- Fix build with mingw

## 23.0.0

Changes:

- all zmq constants are now available as Python enums
  (e.g. `zmq.SocketType.PULL`, `zmq.SocketOption.IDENTITY`),
  generated statically from zmq.h instead of at compile-time.
  This means that checks for the *presence* of a constant (`hasattr(zmq, 'RADIO')`)
  is not a valid check for the presence of a feature.
  This practice has never been robust, but it may have worked sometimes.
  Use direct checks via e.g. {func}`zmq.has` or {func}`zmq.zmq_version_info`.
- A bit more type coverage of Context.term and Context.socket

Compatibility fixes:

- Remove all use of deprecated stdlib distutils
- Update to Cython 0.29.30 (required for Python 3.11 compatibility)
- Compatibility with Python 3.11.0b1

Maintenance changes:

- Switch to myst for docs
- Deprecate `zmq.utils.strtypes`, now unused
- Updates to autoformatting, linting
- New wheels for PyPy 3.9
- Manylinux wheels for CPython 3.10 are based on manylinux2014

## 22.3.0

Fixes:

- Fix `strlcpy` compilation issues on alpine, freebsd.
  Adds new build-time dependency on `packaging`.
- In event-loop integration: warn instead of raise when triggering callback on a socket whose context has been closed.
- Bundled libzmq in wheels backport a patch to avoid crashes
  due to inappropriate closing of libsodium's random generator
  when using CurveZMQ.

Changes:

- New ResourceWarnings when contexts and sockets are closed by garbage collection,
  which can be a source of hangs and leaks (matches open files)

## 22.2.1

Fix bundling of wepoll on Windows.

## 22.2.0

New features:

- IPC support on Windows:
  where available (64bit Windows wheels and bundled libzmq when compiling from source, via wepoll),
  IPC should work on appropriate Windows versions.
- Nicer reprs of contexts and sockets
- Memory allocated by `recv(copy=False)` is no longer read-only
- asyncio: Always reference current loop instead of attaching to the current loop at instantiation time.
  This fixes e.g. contexts and/or sockets instantiated prior to a call to `asyncio.run`.
- ssh: `$PYZMQ_PARAMIKO_HOST_KEY_POLICY` can be used to set the missing host key policy,
  e.g. `AutoAdd`.

Fixes:

- Fix memory corruption in gevent integration
- Fix `memoryview(zmq.Frame)` with cffi backend
- Fix threadsafety issue when closing sockets

Changes:

- pypy Windows wheels are 64b-only, following an update in cibuildwheel 2.0
- deprecate `zmq.utils.jsonapi` and remove support for non-stdlib json implementations in `send/recv_json`.
  Custom serialization methods should be used instead.

## 22.1.0

New features:

- asyncio: experimental support for Proactor eventloop if tornado 6.1 is available
  by running a selector in a background thread.

Fixes:

- Windows: fix type of `socket.FD` option in win-amd64
- asyncio: Cancel timers when using HWM with async Sockets

Other changes:

- Windows: update bundled libzmq dll URLs for Windows.
  Windows wheels no longer include concrt140.dll.
- adopt pre-commit for formatting, linting

## 22.0.3

- Fix fork-safety bug in garbage collection thread (regression in 20.0)
  when using subprocesses.
- Start uploading universal wheels for ARM Macs.

## 22.0.2

- Add workaround for bug in DLL loading for Windows wheels with conda Python >= 3.8

## 22.0.1

- Fix type of `Frame.bytes` for non-copying recvs with CFFI backend (regression in 21.0)
- Add manylinux wheels for pypy

## 22.0.0

This is a major release due to changes in wheels and building on Windows.
Code changes from 21.0 are minimal.

- Some typing fixes
- Bump bundled libzmq to 4.3.4
- Strip unused symbols in manylinux wheels, resulting in dramatically smaller binaries.
  This matches behavior in v20 and earlier.
- Windows CPython wheels bundle public libzmq binary builds,
  instead of building libzmq as a Python Extension.
  This means they include libsodium for the first time.
- Our own implementation of bundling libzmq into pyzmq on Windows is removed,
  instead relying on delvewheel (or installations putting dlls on %PATH%) to bundle dependency dlls.
- The (new in 21.0) Windows wheels for PyPy likely require the Windows vcredist package.
  This may have always been the case, but the delvewheel approach doesn't seem to work.
- Windows + PyPy is now the only remaining case where a wheel has libzmq built as an Extension.
  All other builds ship libzmq built using its own tooling,
  which should result in better, more stable builds.

## 21.0.2

- Fix wheels on macOS older than 10.15 (sets MACOSX_DEPLOYMENT_TARGET to 10.9, matching wheel ABI tag).

## 21.0.1

pyzmq-21.0.1 only changes CI configuration for Windows wheels (built with VS2017 instead of VS2019),
fixing compatibility with some older Windows on all Pythons
and removing requirement of VC++ redistributable package on latest Windows and Python \< 3.8.

There still appears to be a compatibility issue with Windows 7 that will be fixed ASAP.
Until then, you can pin `pip install pyzmq<21`.

There are no changes from 21.0.0 for other platforms.

## 21.0

pyzmq 21 is a major version bump because of dropped support for old Pythons and some changes in packaging.
CPython users should not face major compatibility issues if installation works at all :)
PyPy users may see issues with the new implementation of send/recv.
If you do, please report them!

The big changes are:

- drop support for Python 3.5. Python >= 3.6 is required
- mypy type stubs, which should improve static analysis of pyzmq,
  especially for dynamically defined attributes such as zmq constants.
  These are new! Let us know if you find any issues.
- support for zero-copy and sending bufferables with cffi backend.
  This is experimental! Please report issues.
- More wheels!
  - linux-aarch64 on Python 3.7-3.9
  - wheels for pypy36, 37 on Linux and Windows (previously just mac)

We've totally redone the wheel-building setup, so let us know if you start seeing installation issues!

Packaging updates:

- Require Python >= 3.6, required for good type annotation support
- Wheels for macOS no longer build libzmq as a Python Extension,
  instead 'real' libzmq is built and linked to libsodium,
  bundled with delocate.
  This matches the longstanding behavior of Linux wheels,
  and should result in better performance.
- Add manylinux wheels for linux-aarch64. These bundle an older version of libzmq than the rest.
- Build wheels for python3.8, 3.9 with manylinux2010 instead of manylinux1.
  Wheels for older Pythons will still be built on manylinux1.
- rework cffi backend in setup.py
- All wheels are built on GitHub Actions (most with cibuildwheel) instead of Min's laptop (finally!).

New features:

- zero-copy support in CFFI backend (`send(copy=False)` now does something).
- Support sending any buffer-interface-providing objects in CFFI backend.

Bugs fixed:

- Errors during teardown of asyncio Sockets
- Missing MSVCP140.dll in Python 3.9 wheels on Windows,
  causing vcruntime-redist package to be required to use the Python 3.9 wheels for pyzmq 20.0

## 20.0

20.0 is a major version bump because of dropped support for old Pythons and some changes in packaging,
but there are only small changes for users with relatively recent versions of Python.

Packaging updates:

- Update bundled libzmq to 4.3.3
- Drop support for Python \< 3.5 (all versions of Python \< 3.6 are EOL at time of release)
- Require setuptools to build from source
- Require Cython 0.29 to build from version control (sdists still ship .c files, so will never need Cython)
- Respect \$PKG_CONFIG env for finding libzmq when building from source

New features:

- {meth}`.Socket.bind` and {meth}`.Socket.connect` can now be used as context managers.

Fixes:

- Better error when libzmq is bundled and fails to be loaded.
- Hold GIL while calling `zmq_curve_` functions, which may fix apparent threadsafety issues.

## 19.0.2

- Regenerate Cython sources with 0.29.21 in sdists for compatibility with Python 3.9
- Handle underlying socket being closed in ZMQStream with warning instead of error
- Improvements to socket cleanup during process teardown
- Fix debug-builds on Windows
- Avoid importing ctypes during startup on Windows
- Documentation improvements
- Raise `AttributeError` instead of `ZMQError(EINVAL)` on attempts to read write-only attributes,
  for compatibility with mocking

## 19.0.1

- Fix TypeError during garbage collection
- Fix compilation with some C++ compilers
- Fixes in tests and examples

## 19.0

- Cython backend: Build Cython extensions with language level "3str" (requires Cython 0.29)
- Cython backend: You can now `cimport zmq`
- Asyncio: Fix memory leak in Poller
- Log: Much improved logging in {mod}`zmq.log` (see {doc}`howto/logging`)
- Log: add `python -m zmq.log` entrypoint
- Sources generated with Cython 0.29.15

## 18.1.1

- Fix race condition when shutting down ZAP thread while events are still processing (only affects tests)
- Publish wheels for Python 3.8 on all platforms
- Stop publishing wheels for Python 3.4 on Windows
- Sources generated with Cython 0.29.14

## 18.1.0

- Compatibility with Python 3.8 release candidate by regenerating Cython courses with Cython 0.29.13
- bump bundled libzmq to 4.3.2
- handle cancelled futures in asyncio
- make {meth}`zmq.Context.instance` fork-safe
- fix errors in {meth}`zmq.Context.destroy` when opening and closing many sockets

## 18.0.2

- Compatibility with Python 3.8 prerelease by regenerating Cython sources
  with Cython 0.29.10.
- Fix language_level=2 in Cython sources, for compatibility with Cython 0.30
- Show missing path for ENOENT errors on ipc connections.

## 18.0.1

Fixes installation from source on non-unicode locales with Python 3.
There are no code changes in this release.

## 18.0.0

- Update bundled libzmq to 4.3.1 (fixes CVE-2019-6250)
- Added {func}`~zmq.proxy_steerable` and {class}`zmq.devices.ProxySteerable`
- Added `bind_{in|out|mon}_to_random_port` variants for proxy device methods
- Performance improvements for sends with asyncio
- Fix sending memoryviews/bytearrays with cffi backend

## 17.1.3

- Fix compatibility with tornado 6 (removal of stack_context)

## 17.1.2

- Fix possible hang when working with asyncio
- Remove some outdated workarounds for old Cython versions
- Fix some compilation with custom compilers
- Remove unneeded link of libstdc++ on PyPy

## 17.1.0

- Bump bundled libzmq to 4.2.5
- Improve tornado 5.0 compatibility
  (use {meth}`~tornado.ioloop.IOLoop.current` instead of {meth}`~tornado.ioloop.IOLoop.instance`
  to get default loops in {class}`.ZMQStream` and {class}`.IOLoopAuthenticator`)
- Add support for {func}`.curve_public`
- Remove delayed import of json in `send/recv_json`
- Add {meth}`.Authenticator.configure_curve_callback`
- Various build fixes
- sdist sources generated with Cython 0.28.3
- Stop building wheels for Python 3.4, start building wheels for Python 3.7

## 17.0.0

- Add {meth}`zmq.Socket.send_serialized` and {meth}`zmq.Socket.recv_serialized`
  for sending/receiving messages with custom serialization.

- Add {attr}`zmq.Socket.copy_threshold` and {const}`zmq.COPY_THRESHOLD`.
  Messages smaller than this are always copied, regardless of `copy=False`,
  to avoid overhead of zero-copy bookkeeping on small messages.

- Added visible deprecation warnings to bundled tornado IOLoop.
  Tornado eventloop integration shouldn't be used without a proper tornado install
  since pyzmq 14.

- Allow pyzmq asyncio/tornado integration to run without installing {func}`zmq_poll`
  implementation. The following methods and classes are deprecated and no longer required:

  - {func}`zmq.eventloop.ioloop.install`
  - {class}`zmq.eventloop.ioloop.IOLoop`
  - {func}`zmq.asyncio.install`
  - {class}`zmq.asyncio.ZMQEventLoop`

- Set RPATH correctly when building on macOS.

- Compatibility fixes with tornado 5.0.dev (may not be quite enough for 5.0 final,
  which is not yet released as of pyzmq 17).

- Draft support for CLIENT-SERVER `routing_id` and `group`.

  ```{seealso}
  {ref}`draft`
  ```

## 16.0.4

- Regenerate Cython sources in sdists with Cython 0.27.3,
  fixing builds on CPython 3.7.
- Add warning when using bundled tornado, which was deprecated too quietly in 14.x.

## 16.0.3

- Regenerate Cython sources in sdists with Cython 0.27.2,
  fixing builds on CPython 3.7.

## 16.0.2

- Workaround bug in libzmq-4.2.0 causing EINVAL on poll.

## 16.0.1

- Fix erroneous EAGAIN that could happen on async sockets
- Bundle libzmq 4.1.6

## 16.0

- Support for Python 2.6 and Python 3.2 is dropped. For old Pythons, use {command}`pip install "pyzmq<16"` to get the last version of pyzmq that supports these versions.
- Include zmq.h
- Deprecate `zmq.Stopwatch`. Native Python timing tools can be used instead.
- Better support for using pyzmq as a Cython library
  \- bundle zmq.h when pyzmq bundles libzmq as an extension
  \- add {func}`zmq.get_library_dirs` to find bundled libzmq
- Updates to setup.py for Cython 0.25 compatibility
- Various asyncio/future fixes:
  \- support raw sockets in pollers
  \- allow cancelling async sends
- Fix {meth}`IOLoop.current` in {mod}`zmq.green`

## 15.4

- Load bundled libzmq extension with import rather than CDLL,
  which should fix some manifest issues in certain cases on Windows.
- Avoid installing asyncio sources on Python 2, which confuses some tools that run `python -m compileall`, which reports errors on the Python 3-only files.
- Bundle msvcp.dll in Windows wheels on CPython 3.5,
  which should fix wheel compatibility systems without Visual C++ 2015 redistributable.
- {meth}`zmq.Context.instance` is now threadsafe.
- FIX: sync some behavior in zmq_poll and setting LINGER on close/destroy with the CFFI backend.
- PERF: resolve send/recv immediately if events are available in async Sockets
- Async Sockets (asyncio, tornado) now support `send_json`, `send_pyobj`, etc.
- add preliminary support for `zmq.DRAFT_API` reflecting ZMQ_BUILD_DRAFT_API,
  which indicates whether new APIs in prereleases are available.

## 15.3

- Bump bundled libzmq to 4.1.5, using tweetnacl for bundled curve support instead of libsodium
- FIX: include .pxi includes in installation for consumers of Cython API
- FIX: various fixes in new async sockets
- Introduce {mod}`zmq.decorators` API for decorating functions to create sockets or contexts
- Add {meth}`zmq.Socket.subscribe` and {meth}`zmq.Socket.unsubscribe` methods to sockets, so that assignment is no longer needed for subscribing. Verbs should be methods!
  Assignment is still supported for backward-compatibility.
- Accept text (unicode) input to z85 encoding, not just bytes
- {meth}`zmq.Context.socket` forwards keyword arguments to the {class}`Socket` constructor

## 15.2

- FIX: handle multiple events in a single register call in {mod}`zmq.asyncio`
- FIX: unicode/bytes bug in password prompt in {mod}`zmq.ssh` on Python 3
- FIX: workaround gevent monkeypatches in garbage collection thread
- update bundled minitornado from tornado-4.3.
- improved inspection by setting `binding=True` in cython compile options
- add asyncio Authenticator implementation in {mod}`zmq.auth.asyncio`
- workaround overflow bug in libzmq preventing receiving messages larger than `MAX_INT`

## 15.1

- FIX: Remove inadvertent tornado dependency when using {mod}`zmq.asyncio`
- FIX: 15.0 Python 3.5 wheels didn't work on Windows
- Add GSSAPI support to Authenticators
- Support new constants defined in upcoming libzmq-4.2.dev

## 15.0

PyZMQ 15 adds Future-returning sockets and pollers for both {mod}`asyncio` and {mod}`tornado`.

- add {mod}`asyncio` support via {mod}`zmq.asyncio`
- add {mod}`tornado` future support via {mod}`zmq.eventloop.future`
- trigger bundled libzmq if system libzmq is found to be \< 3.
  System libzmq 2 can be forced by explicitly requesting `--zmq=/prefix/`.

## 14.7.0

Changes:

- Update bundled libzmq to 4.1.2.
- Following the [lead of Python 3.5](https://www.python.org/dev/peps/pep-0475/),
  interrupted system calls will be retried.

Fixes:

- Fixes for CFFI backend on Python 3 + support for PyPy 3.
- Verify types of all frames in {meth}`~zmq.Socket.send_multipart` before sending,
  to avoid partial messages.
- Fix build on Windows when both debug and release versions of libzmq are found.
- Windows build fixes for Python 3.5.

## 14.6.0

Changes:

- improvements in {meth}`zmq.Socket.bind_to_random_port`:
  : - use system to allocate ports by default
  - catch EACCES on Windows
- include libsodium when building bundled libzmq on Windows (includes wheels on PyPI)
- pyzmq no longer bundles external libzmq when making a bdist.
  You can use [delocate](https://pypi.org/project/delocate/) to do this.

Bugfixes:

- add missing {attr}`ndim` on memoryviews of Frames
- allow {func}`copy.copy` and {func}`copy.deepcopy` on Sockets, Contexts

## 14.5.0

Changes:

- use pickle.DEFAULT_PROTOCOL by default in send_pickle
- with the release of pip-6, OS X wheels are only marked as 10.6-intel,
  indicating that they should be installable on any newer or single-arch Python.
- raise SSHException on failed check of host key

Bugfixes:

- fix method name in utils.wi32.allow_interrupt
- fork-related fixes in garbage collection thread
- add missing import in `zmq.__init__`, causing failure to import in some circumstances

## 14.4.1

Bugfixes for 14.4

- SyntaxError on Python 2.6 in zmq.ssh
- Handle possible bug in garbage collection after fork

## 14.4.0

New features:

- Experimental support for libzmq-4.1.0 rc (new constants, plus {func}`zmq.has`).
- Update bundled libzmq to 4.0.5
- Update bundled libsodium to 1.0.0
- Fixes for SSH dialogs when using {mod}`zmq.ssh` to create tunnels
- More build/link/load fixes on OS X and Solaris
- Get Frame metadata via dict access (libzmq 4)
- Contexts and Sockets are context managers (term/close on `__exit__`)
- Add {class}`zmq.utils.win32.allow_interrupt` context manager for catching SIGINT on Windows

Bugs fixed:

- Bundled libzmq should not trigger recompilation after install on PyPy

## 14.3.1

```{note}
pyzmq-14.3.1 is the last version to include bdists for Python 3.3
```

Minor bugfixes to pyzmq 14.3:

- Fixes to building bundled libzmq on OS X \< 10.9
- Fixes to import-failure warnings on Python 3.4
- Fixes to tests
- Pull upstream fixes to zmq.ssh for ssh multiplexing

## 14.3.0

- PyZMQ no longer calls {meth}`.Socket.close` or {meth}`.Context.term` during process cleanup.
  Changes to garbage collection in Python 3.4 make this impossible to do sensibly.
- {meth}`ZMQStream.close` closes its socket immediately, rather than scheduling a timeout.
- Raise the original ImportError when importing zmq fails.
  Should be more informative than `no module cffi...`.

```{warning}
Users of Python 3.4 should not use pyzmq \< 14.3, due to changes in garbage collection.
```

## 14.2.0

### New Stuff

- Raise new ZMQVersionError when a requested method is not supported by the linked libzmq.
  For backward compatibility, this subclasses NotImplementedError.

### Bugs Fixed

- Memory leak introduced in pyzmq-14.0 in zero copy.
- OverflowError on 32 bit systems in zero copy.

## 14.1.0

### Security

The headline features for 14.1 are adding better support for libzmq's
security features.

- When libzmq is bundled as a Python extension (e.g. wheels, eggs),
  libsodium is also bundled (excluding Windows),
  ensuring that libzmq security is available to users who install from wheels
- New {mod}`zmq.auth`, implementing zeromq's ZAP authentication,
  modeled on czmq zauth.
  For more information, see the [examples](https://github.com/zeromq/pyzmq/tree/HEAD/examples/).

### Other New Stuff

- Add PYZMQ_BACKEND for enabling use of backends outside the pyzmq codebase.
- Add {attr}`~.Context.underlying` property and {meth}`~.Context.shadow`
  method to Context and Socket, for handing off sockets and contexts.
  between pyzmq and other bindings (mainly [pyczmq]).
- Add TOS, ROUTER_HANDOVER, and IPC_FILTER constants from libzmq-4.1-dev.
- Add Context option support in the CFFI backend.
- Various small unicode and build fixes, as always.
- {meth}`~.Socket.send_json` and {meth}`~.Socket.recv_json` pass any extra kwargs to `json.dumps/loads`.

### Deprecations

- `Socket.socket_type` is deprecated, in favor of `Socket.type`,
  which has been available since 2.1.

## 14.0.1

Bugfix release

- Update bundled libzmq to current (4.0.3).
- Fix bug in {meth}`.Context.destroy` with no open sockets.
- Threadsafety fixes in the garbage collector.
- Python 3 fixes in {mod}`zmq.ssh`.

## 14.0.0

- Update bundled libzmq to current (4.0.1).
- Backends are now implemented in `zmq.backend` instead of `zmq.core`.
  This has no effect on public APIs.
- Various build improvements for Cython and CFFI backends (PyPy compiles at build time).
- Various GIL-related performance improvements - the GIL is no longer touched from a zmq IO thread.
- Adding a constant should now be a bit easier - only zmq/sugar/constant_names should need updating,
  all other constant-related files should be automatically updated by `setup.py constants`.
- add support for latest libzmq-4.0.1
  (includes ZMQ_CURVE security and socket event monitoring).

### New stuff

- {meth}`.Socket.monitor`
- {meth}`.Socket.get_monitor_socket`
- {func}`zmq.curve_keypair`
- {mod}`zmq.utils.monitor`
- {mod}`zmq.utils.z85`

## 13.1.0

The main new feature is improved tornado 3 compatibility.
PyZMQ ships a 'minitornado' submodule, which contains a small subset of tornado 3.0.1,
in order to get the IOLoop base class.  zmq.eventloop.ioloop.IOLoop is now a simple subclass,
and if the system tornado is ≥ 3.0, then the zmq IOLoop is a proper registered subclass
of the tornado one itself, and minitornado is entirely unused.

## 13.0.2

Bugfix release!

A few things were broken in 13.0.0, so this is a quick bugfix release.

- **FIXED** EAGAIN was unconditionally turned into KeyboardInterrupt
- **FIXED** we used totally deprecated ctypes_configure to generate constants in CFFI backend
- **FIXED** memory leak in CFFI backend for PyPy
- **FIXED** typo prevented IPC_PATH_MAX_LEN from ever being defined
- **FIXED** various build fixes - linking with librt, Cython compatibility, etc.

## 13.0.1

defunct bugfix. We do not speak of this...

## 13.0.0

PyZMQ now officially targets libzmq-3 (3.2.2),
0MQ ≥ 2.1.4 is still supported for the indefinite future, but 3.x is recommended.
PyZMQ has detached from libzmq versioning,
and will just follow its own regular versioning scheme from now on.
PyZMQ bdists will include whatever is the latest stable libzmq release (3.2.2 for pyzmq-13.0).

```{note}
set/get methods are exposed via get/setattr on all Context, Socket, and Frame classes.
This means that subclasses of these classes that require extra attributes
**must declare these attributes at the class level**.
```

### Experiments Removed

- The Threadsafe ZMQStream experiment in 2.2.0.1 was deemed inappropriate and not useful,
  and has been removed.
- The {mod}`zmq.web` experiment has been removed,
  to be developed as a [standalone project](https://github.com/ellisonbg/zmqweb).

### New Stuff

- Support for PyPy via CFFI backend (requires py, ctypes-configure, and cffi).

- Add support for new APIs in libzmq-3

  - {meth}`.Socket.disconnect`
  - {meth}`.Socket.unbind`
  - {meth}`.Context.set`
  - {meth}`.Context.get`
  - {meth}`.Frame.set`
  - {meth}`.Frame.get`
  - {func}`zmq.proxy`
  - {class}`zmq.devices.Proxy`
  - Exceptions for common zmq errnos: {class}`zmq.Again`, {class}`zmq.ContextTerminated`
    (subclass {class}`ZMQError`, so fully backward-compatible).

- Setting and getting {attr}`.Socket.hwm` sets or gets *both* SNDHWM/RCVHWM for libzmq-3.

- Implementation splits core Cython bindings from pure-Python subclasses
  with sugar methods (send/recv_multipart). This should facilitate
  non-Cython backends and PyPy support \[spoiler: it did!\].

### Bugs Fixed

- Unicode fixes in log and monitored queue
- MinGW, ppc, cross-compilation, and HP-UX build fixes
- {mod}`zmq.green` should be complete - devices and tornado eventloop both work
  in gevent contexts.

## 2.2.0.1

This is a tech-preview release, to try out some new features.
It is expected to be short-lived, as there are likely to be issues to iron out,
particularly with the new pip-install support.

### Experimental New Stuff

These features are marked 'experimental', which means that their APIs are not set in stone,
and may be removed or changed in incompatible ways in later releases.

#### Threadsafe ZMQStream

With the IOLoop inherited from tornado, there is exactly one method that is threadsafe:
{meth}`.IOLoop.add_callback`.  With this release, we are trying an experimental option
to pass all IOLoop calls via this method, so that ZMQStreams can be used from one thread
while the IOLoop runs in another.  To try out a threadsafe stream:

```python
stream = ZMQStream(socket, threadsafe=True)
```

#### pip install pyzmq

PyZMQ should now be pip installable, even on systems without libzmq.
In these cases, when pyzmq fails to find an appropriate libzmq to link against,
it will try to build libzmq as a Python extension.
This work is derived from [pyzmq_static](https://github.com/brandon-rhodes/pyzmq-static).

To this end, PyZMQ source distributions include the sources for libzmq (2.2.0) and libuuid (2.21),
both used under the LGPL.

#### zmq.green

The excellent [gevent_zeromq](https://github.com/tmc/gevent-zeromq) socket
subclass which provides [gevent](https://www.gevent.org/) compatibility has been merged as
{mod}`zmq.green`.

```{seealso}
{mod}`zmq.green`
```

### Bugs Fixed

- TIMEO sockopts are properly included for libzmq-2.2.0
- avoid garbage collection of sockets after fork (would cause `assert (mailbox.cpp:79)`).

## 2.2.0

Some effort has gone into refining the pyzmq API in this release to make it a model for
other language bindings.  This is principally made in a few renames of objects and methods,
all of which leave the old name for backwards compatibility.

```{note}
As of this release, all code outside `zmq.core` is BSD licensed (where
possible), to allow more permissive use of less-critical code and utilities.
```

### Name Changes

- The {class}`~.Message` class has been renamed to {class}`~.Frame`, to better match other
  zmq bindings. The old Message name remains for backwards-compatibility.  Wherever pyzmq
  docs say "Message", they should refer to a complete zmq atom of communication (one or
  more Frames, connected by ZMQ_SNDMORE). Please report any remaining instances of
  Message==MessagePart with an Issue (or better yet a Pull Request).
- All `foo_unicode` methods are now called `foo_string` (`_unicode` remains for
  backwards compatibility).  This is not only for cross-language consistency, but it makes
  more sense in Python 3, where native strings are unicode, and the `_unicode` suffix
  was wedded too much to Python 2.

### Other Changes and Removals

- `prefix` removed as an unused keyword argument from {meth}`~.Socket.send_multipart`.
- ZMQStream {meth}`~.ZMQStream.send` default has been changed to `copy=True`, so it matches
  Socket {meth}`~.Socket.send`.
- ZMQStream {meth}`~.ZMQStream.on_err` is deprecated, because it never did anything.
- Python 2.5 compatibility has been dropped, and some code has been cleaned up to reflect
  no-longer-needed hacks.
- Some Cython files in {mod}`zmq.core` have been split, to reduce the amount of
  Cython-compiled code.  Much of the body of these files were pure Python, and thus did
  not benefit from the increased compile time.  This change also aims to ease maintaining
  feature parity in other projects, such as
  [pyzmq-ctypes](https://github.com/svpcom/pyzmq-ctypes).

### New Stuff

- {class}`~.Context` objects can now set default options when they create a socket. These
  are set and accessed as attributes to the context.  Socket options that do not apply to a
  socket (e.g. SUBSCRIBE on non-SUB sockets) will simply be ignored.
- {meth}`~.ZMQStream.on_recv_stream` has been added, which adds the stream itself as a
  second argument to the callback, making it easier to use a single callback on multiple
  streams.
- A {attr}`~Frame.more` boolean attribute has been added to the {class}`~.Frame` (née
  Message) class, so that frames can be identified as terminal without extra queries of
  {attr}`~.Socket.rcvmore`.

### Experimental New Stuff

These features are marked 'experimental', which means that their APIs are not
set in stone, and may be removed or changed in incompatible ways in later releases.

- {mod}`zmq.web` added for load-balancing requests in a tornado webapp with zeromq.

## 2.1.11

- remove support for LABEL prefixes.  A major feature of libzmq-3.0, the LABEL
  prefix, has been removed from libzmq, prior to the first stable libzmq 3.x release.

  - The prefix argument to {meth}`~.Socket.send_multipart` remains, but it continue to behave in
    exactly the same way as it always has on 2.1.x, simply prepending message parts.
  - {meth}`~.Socket.recv_multipart` will always return a list, because prefixes are once
    again indistinguishable from regular message parts.

- add {meth}`.Socket.poll` method, for simple polling of events on a single socket.

- no longer require monkeypatching tornado IOLoop.  The {class}`.ioloop.ZMQPoller` class
  is a poller implementation that matches tornado's expectations, and pyzmq sockets can
  be used with any tornado application just by specifying the use of this poller.  The
  pyzmq IOLoop implementation now only trivially differs from tornado's.

  It is still recommended to use {func}`.ioloop.install`, which sets *both* the zmq and
  tornado global IOLoop instances to the same object, but it is no longer necessary.

  ```{warning}
  The most important part of this change is that the `IOLoop.READ/WRITE/ERROR`
  constants now match tornado's, rather than being mapped directly to the zmq
  `POLLIN/OUT/ERR`. So applications that used the low-level {meth}`IOLoop.add_handler`
  code with `POLLIN/OUT/ERR` directly (used to work, but was incorrect), rather than
  using the IOLoop class constants will no longer work. Fixing these to use the IOLoop
  constants should be insensitive to the actual value of the constants.
  ```

## 2.1.10

- Add support for libzmq-3.0 LABEL prefixes:

  ```{warning}
  This feature has been removed from libzmq, and thus removed from future pyzmq
  as well.
  ```

  - send a message with label-prefix with:

    ```python
    send_multipart([b"msg", b"parts"], prefix=[b"label", b"prefix"])
    ```

  - {meth}`recv_multipart` returns a tuple of `(prefix,msg)` if a label prefix is detected

  - ZMQStreams and devices also respect the LABEL prefix

- add czmq-style close&term as {meth}`ctx.destroy`, so that {meth}`ctx.term`
  remains threadsafe and 1:1 with libzmq.

- {meth}`Socket.close` takes optional linger option, for setting linger prior
  to closing.

- add {func}`~zmq.core.version.zmq_version_info` and
  {func}`~zmq.core.version.pyzmq_version_info` for getting libzmq and pyzmq versions as
  tuples of numbers. This helps with the fact that version string comparison breaks down
  once versions get into double-digits.

- ioloop changes merged from upstream [Tornado](https://www.tornadoweb.org) 2.1

## 2.1.9

- added zmq.ssh tools for tunneling socket connections, copied from IPython
- Expanded sockopt support to cover changes in libzmq-4.0 dev.
- Fixed an issue that prevented {exc}`KeyboardInterrupts` from being catchable.
- Added attribute-access for set/getsockopt.  Setting/Getting attributes of {class}`Sockets`
  with the names of socket options is mapped to calls of set/getsockopt.

```python
s.hwm = 10
s.identity = b"whoda"
s.linger
# -1
```

- Terminating a {class}`~Context` closes the sockets it created, matching the behavior in
  [czmq](http://czmq.zeromq.org/).
- {class}`ThreadDevices` use {meth}`Context.instance` to create sockets, so they can use
  inproc connections to sockets in other threads.
- fixed units error on {func}`zmq.select`, where the poll timeout was 1000 times longer
  than expected.
- Add missing `DEALER/ROUTER` socket type names (currently aliases, to be replacements for `XREP/XREQ`).
- base libzmq dependency raised to 2.1.4 (first stable release) from 2.1.0.

## 2.1.7.1

- bdist for 64b Windows only.  This fixed a type mismatch on the `ZMQ_FD` sockopt
  that only affected that platform.

## 2.1.7

- Added experimental support for libzmq-3.0 API
- Add {func}`zmq.eventloop.ioloop.install` for using pyzmq's IOLoop in a tornado
  application.

## 2.1.4

- First version with binary distribution support
- Added {meth}`~Context.instance()` method for using a single Context throughout an application
  without passing references around.

[cython-build-requires]: https://groups.google.com/g/cython-users/c/ZqKFQmS0JdA/m/1FrK1ApYBAAJ
[pyczmq]: https://github.com/zeromq/pyczmq
[scikit-build-core]: https://scikit-build-core.readthedocs.io
