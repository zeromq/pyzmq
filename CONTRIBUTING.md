# Opening an Issue

For a good bug report:

1. [Search][] for existing Issues, both on GitHub and in general with Google/Stack Overflow before posting a duplicate question.
2. Update to pyzmq master, if possible, especially if you are already using git. It's
   possible that the bug you are about to report has already been fixed.

Many things reported as pyzmq Issues are often just libzmq-related,
and don't have anything to do with pyzmq itself.
These are better directed to [zeromq-dev][].

When making a bug report, it is helpful to tell us as much as you can about your system
(such as pyzmq version, libzmq version, Python version, OS Version, how you built/installed pyzmq and libzmq, etc.)

The basics:

```python
import sys
import zmq

print "libzmq-%s" % zmq.zmq_version()
print "pyzmq-%s" % zmq.pyzmq_version()
print "Python-%s" % sys.version
```

Which will give something like:

    libzmq-3.3.0
    pyzmq-2.2dev
    Python-2.7.2 (default, Jun 20 2012, 16:23:33) 
    [GCC 4.2.1 Compatible Apple Clang 4.0 (tags/Apple/clang-418.0.60)]

[search]: https://github.com/zeromq/pyzmq/issues
[zeromq-dev]: mailto:zeromq-dev@zeromq.org


# Licensing and contributing to PyZMQ

PyZMQ uses different licenses for different parts of the code.

The 'core' of PyZMQ (located in zmq/core) is licensed under LGPLv3.
This just  means that if you make any changes to how that code works,
you must release  those changes under the LGPL.
If you just *use* pyzmq, then you can use any license you want for your own code.

We don't feel that the restrictions imposed by the LGPL make sense for the 
'non-core' functionality in pyzmq (derivative code must *also* be LGPL or GPL), 
especially for examples and utility code, so we have relicensed all 'non-core' 
code under the more permissive BSD (specifically Modified BSD aka New BSD aka 
3-clause BSD), where possible. This means that you can copy this code and build 
your own apps without needing to license your own code with the LGPL or GPL.

## Your contributions

**Pull Requests are welcome!**

When you contribute to PyZMQ, your contributions are made under the same 
license as the file you are working on. Any new, original code should be BSD 
licensed.

We don't enforce strict style, but when in doubt [PEP8][] is a good guideline.
The only thing we really don't like is mixing up 'cleanup' in real work.

Examples are copyright their respective authors, and BSD unless otherwise 
specified by the author. You can LGPL (or GPL or MIT or Apache, etc.) your own new 
examples if you like, but we strongly encourage using the default BSD license.

[PEP8]: http://www.python.org/dev/peps/pep-0008

## Inherited licenses in pyzmq

Some code outside the core is taken from other open-source projects, and 
inherits that project's license.

* zmq/eventloop contains files inherited and adapted from [tornado][], and inherits the Apache license

* zmq/ssh/forward.py is from [paramiko][], and inherits LGPL

* zmq/devices/monitoredqueue.pxd is derived from the zmq_device function in 
libzmq, and inherits LGPL

* perf examples are (c) iMatix, and LGPL

[tornado]: http://www.tornadoweb.org
[paramiko]: http://www.lag.net/paramiko