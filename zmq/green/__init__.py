# -*- coding: utf-8 -*-
"""zmq.green - gevent compatibility with zeromq.

Usage
-----

Instead of importing zmq directly, do so in the following manner:

..

    import zmq.green as zmq


Any calls that would have blocked the current thread will now only block the
current green thread.

This compatibility is accomplished by ensuring the nonblocking flag is set
before any blocking operation and the ØMQ file descriptor is polled internally
to trigger needed events.
"""

from zmq import *
from zmq.green.core import _Context, _Socket
Context = _Context
Socket = _Socket

