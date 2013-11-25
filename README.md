# PyZMQ: Python bindings for ØMQ


This package contains Python bindings for [ØMQ](http://www.zeromq.org).
ØMQ is a lightweight and fast messaging implementation.

PyZMQ should work with any Python ≥ 2.6 (including Python 3), as well as PyPy.
The Cython backend used by CPython supports libzmq ≥ 2.1.4 (including 3.2.x and 4.x),
but the CFFI backend used by PyPy only supports libzmq ≥ 3.2.2 (including 4.x).

## Versioning

Current release of pyzmq is 14.0.1, and targets libzmq-4.0.3.
For libzmq 2.0.x, use pyzmq release 2.0.10.1 or the 2.0.x maintenance branch.
PyZMQ (on CPython via Cython) continues to support libzmq ≥ 2.1.4.

pyzmq-2.1.11 was the last version of pyzmq to support Python 2.5,
and pyzmq ≥ 2.2.0 requires Python ≥ 2.6.
pyzmq-13.0.0 introduces PyPy support via CFFI, which only supports libzmq-3.2.2 and newer.

PyZMQ releases ≤ 2.2.0 matched libzmq versioning, but this is no longer the case,
starting with PyZMQ 13.0.0 (it was the thirteenth release, so why not?).
PyZMQ ≥ 13.0 follows semantic versioning conventions accounting only for PyZMQ itself.

For a summary of changes to pyzmq, see our
[changelog](http://zeromq.github.com/pyzmq/changelog.html).

### ØMQ 3.x, 4.x

PyZMQ ≥ 2.2.0 fully supports the 3.x and 4.x APIs of libzmq,
developed at [zeromq/libzmq](https://github.com/zeromq/libzmq).
No code to change, no flags to pass,
just build pyzmq against the latest and it should work.

PyZMQ on PyPy *only* supports libzmq >= 3.2.2.

## Documentation

See PyZMQ's Sphinx-generated
[documentation](http://zeromq.github.com/pyzmq) on GitHub for API
details, and some notes on Python and Cython development. If you want to
learn about using ØMQ in general, the excellent [ØMQ
Guide](http://zguide.zeromq.org) is the place to start, which has a
Python version of every example. We also have some information on our
[wiki](https://github.com/zeromq/pyzmq/wiki)

## Downloading

Unless you specifically want to develop PyZMQ, we recommend downloading
the PyZMQ source code, eggs, or MSI installer from
[PyPI](http://pypi.python.org/pypi/pyzmq).

You can also get the latest source code from our GitHub repository, but
building from the repository will require that you install Cython
version 0.16 or later.

## Building and installation

For more detail on building pyzmq, see [our Wiki](https://github.com/zeromq/pyzmq/wiki/Building-and-Installing-PyZMQ).

We build eggs and wheels for OS X and Windows, so you can get a binary on those platforms with either:

    easy_install pyzmq

or

    pip install --use-wheel pyzmq

But compiling from source with `pip install pyzmq` should work in most environments.

To build pyzmq from the git repo (including release tags) requires Cython.

