# PyZMQ: Python bindings for ØMQ

[![Build Status](https://travis-ci.org/zeromq/pyzmq.svg?branch=master)](https://travis-ci.org/zeromq/pyzmq)

[![Windows Build status](https://ci.appveyor.com/api/projects/status/ugoid0r2fnq8sr56/branch/master?svg=true)](https://ci.appveyor.com/project/minrk/pyzmq/branch/master)

This package contains Python bindings for [ØMQ](http://www.zeromq.org).
ØMQ is a lightweight and fast messaging implementation.

PyZMQ should work with any reasonable version of Python (≥ 3.4),
as well as Python 2.7 and PyPy.
The Cython backend used by CPython supports libzmq ≥ 2.1.4 (including 3.2.x and 4.x),
but the CFFI backend used by PyPy only supports libzmq ≥ 3.2.2 (including 4.x).

For a summary of changes to pyzmq, see our
[changelog](https://pyzmq.readthedocs.org/en/latest/changelog.html).

### ØMQ 3.x, 4.x

PyZMQ fully supports the 3.x and 4.x APIs of libzmq,
developed at [zeromq/libzmq](https://github.com/zeromq/libzmq).
No code to change, no flags to pass,
just build pyzmq against the latest and it should work.

PyZMQ does not support the old libzmq 2 API on PyPy.

## Documentation

See PyZMQ's Sphinx-generated
[documentation](https://zeromq.github.io/pyzmq) on GitHub for API
details, and some notes on Python and Cython development. If you want to
learn about using ØMQ in general, the excellent [ØMQ
Guide](http://zguide.zeromq.org/py:all) is the place to start, which has a
Python version of every example. We also have some information on our
[wiki](https://github.com/zeromq/pyzmq/wiki).

## Downloading

Unless you specifically want to develop PyZMQ, we recommend downloading
the PyZMQ source code or wheels from
[PyPI](https://pypi.io/projects/pyzmq),
or install with conda.

You can also get the latest source code from our GitHub repository, but
building from the repository will require that you install recent Cython.

## Building and installation

For more detail on building pyzmq, see [our Wiki](https://github.com/zeromq/pyzmq/wiki/Building-and-Installing-PyZMQ).

We build wheels for OS X, Windows, and Linux, so you can get a binary on those platforms with:

    pip install pyzmq

but compiling from source with `pip install pyzmq` should work in most environments.
Especially on OS X, make sure you are using the latest pip (≥ 8), or it may not find the right wheels.

If the wheel doesn't work for some reason, or you want to force pyzmq to be compiled
(this is often preferable if you already have libzmq installed and configured the way you want it),
you can force installation with:

    pip install --no-use-wheel pyzmq

When compiling pyzmq (e.g. installing with pip on Linux),
it is generally recommended that zeromq be installed separately,
via homebrew, apt, yum, etc:

    # Debian-based
    sudo apt-get install libzmq3-dev

    # RHEL-based
    sudo yum install libzmq3-devel

If this is not available, pyzmq will *try* to build libzmq as a Python Extension,
though this is not guaranteed to work.

Building pyzmq from the git repo (including release tags on GitHub) requires Cython.

## Old versions

pyzmq 17 drops support Python 3.3.
If you need to use Python 3.3, you can pin your pyzmq version to before 17:

    pip install 'pyzmq<17'

pyzmq 16 drops support Python 2.6 and 3.2.
If you need to use one of those Python versions, you can pin your pyzmq version to before 16:

    pip install 'pyzmq<16'

For libzmq 2.0.x, use 'pyzmq<2.1'

pyzmq-2.1.11 was the last version of pyzmq to support Python 2.5,
and pyzmq ≥ 2.2.0 requires Python ≥ 2.6.
pyzmq-13.0.0 introduces PyPy support via CFFI, which only supports libzmq-3.2.2 and newer.

PyZMQ releases ≤ 2.2.0 matched libzmq versioning, but this is no longer the case,
starting with PyZMQ 13.0.0 (it was the thirteenth release, so why not?).
PyZMQ ≥ 13.0 follows semantic versioning conventions accounting only for PyZMQ itself.

