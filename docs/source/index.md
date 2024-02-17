---
Date: '{{ today }}'
Release: '{{ release }}'
---

# PyZMQ Documentation

PyZMQ is the Python bindings for [ØMQ].
This documentation currently contains notes on some important aspects of developing PyZMQ and
an overview of what the ØMQ API looks like in Python. For information on how to use
ØMQ in general, see the many examples in the excellent [ØMQ Guide], all of which
have a version in Python.

PyZMQ works with Python 3 (≥ 3.7), as well as PyPy via CFFI.

Please don't hesitate to report pyzmq-specific issues to our [tracker] on GitHub.
General questions about ØMQ are better sent to the [ØMQ tracker] or [mailing list].

{doc}`changelog`

# Supported LibZMQ

PyZMQ aims to support all stable (≥ 3.2.2, ≥ 4.0.1 )
versions of libzmq.  Building the same pyzmq against various versions of libzmq is supported,
but only the functionality of the linked libzmq will be available.

```{note}
libzmq 3.0-3.1 are not supported,
as they never received a stable release.
```

Binary distributions (wheels on [PyPI](https://pypi.org/project/pyzmq/)) of PyZMQ ship with
the stable version of libzmq at the time of release, built with default configuration,
and include CURVE support provided by libsodium.
For pyzmq-{{ release }}, this is {{ target_libzmq }}.

# Using PyZMQ

To get started with ZeroMQ, read [the ZeroMQ guide](https://zguide.zeromq.org),
which has every example implemented using PyZMQ.

You can also check out the [examples in the pyzmq repo](https://github.com/zeromq/pyzmq/tree/HEAD/examples).

```{toctree}
---
maxdepth: 2
---
api/index.rst
changelog.rst
howto/index.rst
notes/index.rst
```

# Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`

# Links

- [ØMQ] Home
- The [ØMQ Guide]
- PyZMQ on [GitHub]
- Issue [Tracker]

[github]: https://github.com/zeromq/pyzmq
[mailing list]: http://wiki.zeromq.org/docs:mailing-lists
[tracker]: https://github.com/zeromq/pyzmq/issues
[ømq]: https://zeromq.org/
[ømq guide]: https://zguide.zeromq.org
[ømq tracker]: https://github.com/zeromq/libzmq/issues
