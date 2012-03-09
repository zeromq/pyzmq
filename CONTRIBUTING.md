# Licensing and contributing to PyZMQ

PyZMQ uses different licenses for different parts of the code.

The 'core' of PyZMQ (located in zmq/core) is licensed under LGPLv3. This just 
means that if you make any changes to how that code works, you must release 
those changes under the LGPL. If you just *use* pyzmq, then you can use any 
license you want for your own code.

We don't feel that the restrictions imposed by the LGPL make sense for the 
'non-core' functionality in pyzmq (derivative code must *also* be LGPL or GPL), 
especially for examples and utility code, so we have relicensed all 'non-core' 
code under the more permissive BSD (specifically Modified BSD aka New BSD aka 
3-clause BSD), where possible. This means that you can copy this code and build 
your own apps without needing to license your own code with the LGPL or GPL.

## Your contributions

When you contribute to PyZMQ, your contributions are made under the same 
license as the file you are working on. Any new original code should be BSD 
licensed.

Examples are copyright their respective authors, and BSD unless otherwise 
specified by the author. You can LGPL (or GPL or MIT or Apache, etc.) your own new 
examples if you like, but we strongly encourage using the default BSD license.

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