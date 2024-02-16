# Testing

pyzmq is tested on GitHub Actions.

![Build Status](https://github.com/zeromq/pyzmq/actions/workflows/test.yml/badge.svg)\](https://github.com/zeromq/pyzmq/actions/workflows/test.yml)

## Opening an Issue

For a good bug report:

1. [Search] for existing Issues, both on GitHub and in general with Google/Stack Overflow before posting a duplicate question.
1. Update to pyzmq main, if possible, especially if you are already using git. It's
   possible that the bug you are about to report has already been fixed.

Many things reported as pyzmq Issues are often just libzmq-related,
and don't have anything to do with pyzmq itself.
These are better directed to [zeromq-dev].

When making a bug report, it is helpful to tell us as much as you can about your system
(such as pyzmq version, libzmq version, Python version, OS Version, how you built/installed pyzmq and libzmq, etc.)

The basics:

```python
import sys
import zmq

print("libzmq-%s" % zmq.zmq_version())
print("pyzmq-%s" % zmq.pyzmq_version())
print("Python-%s" % sys.version)
```

Which will give something like:

```
libzmq-4.3.4
pyzmq-22.3.0
Python-3.9.9 | packaged by conda-forge | (main, Dec 20 2021, 02:38:53)
[Clang 11.1.0 ]
```

### Your contributions

**Pull Requests are welcome!**

When you contribute to PyZMQ, your contributions are made under the same
license as the file you are working on. Any new, original code should be BSD
licensed.

We use [pre-commit] for autoformatting,
so you hopefully don't need to worry too much about style.

To install pre-commit:

```
pip install pre-commit
pre-commit install
```

Examples are copyright their respective authors, and BSD unless otherwise
specified by the author.

### Inherited licenses in pyzmq

Some code outside the core is taken from other open-source projects, and
inherits that project's license.

- zmq/eventloop contains files inherited and adapted from [tornado], and inherits the Apache license

- zmq/ssh/forward.py is from [paramiko], and inherits LGPL

- perf examples are (c) iMatix, and MPL

[paramiko]: http://www.lag.net/paramiko
[pre-commit]: https://pre-commit.com
[search]: https://github.com/zeromq/pyzmq/issues
[tornado]: http://www.tornadoweb.org
[zeromq-dev]: mailto:zeromq-dev@zeromq.org
