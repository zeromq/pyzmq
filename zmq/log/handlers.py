#!/usr/bin/env python
"""pyzmq logging handlers.

This mainly defines the PUBHandler object for publishing logging messages over
a zmq.PUB socket.

The PUBHandler can be used with the regular logging module, as in::

    >>> import logging
    >>> handler = PUBHandler('tcp://127.0.0.1:12345')
    >>> handler.root_topic = 'foo'
    >>> logger = logging.getLogger('foobar')
    >>> logger.addHandler(logging.DEBUG, handler)

After this point, all messages logged by ``logger`` will be published on the
PUB socket.

Code adapted from StarCluster:

    http://github.com/jtriley/StarCluster/blob/master/starcluster/logger.py

Authors
-------
* Min RK
"""

#
#    Copyright (c) 2010 Min Ragan-Kelley
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import logging
from logging import INFO, DEBUG, WARN, ERROR, FATAL

import zmq
from zmq.utils.strtypes import bytes,unicode

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

TOPIC_DELIM="::" # delimiter for splitting topics on the receiving end.


class PUBHandler(logging.Handler):
    """A basic logging handler that emits log messages through a PUB socket.

    Takes a PUB socket already bound to interfaces or an interface to bind to.

    Example::

        sock = context.socket(zmq.PUB)
        sock.bind('inproc://log')
        handler = PUBHandler(sock)

    Or::

        handler = PUBHandler('inproc://loc')

    These are equivalent.

    Log messages handled by this handler are broadcast with ZMQ topics
    ``this.root_topic`` comes first, followed by the log level
    (DEBUG,INFO,etc.), followed by any additional subtopics specified in the
    message by: log.debug("subtopic.subsub::the real message")
    """
    root_topic="".encode()
    socket = None
    
    formatters = {
        logging.DEBUG: logging.Formatter(
        "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"),
        logging.INFO: logging.Formatter("%(message)s\n"),
        logging.WARN: logging.Formatter(
        "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"),
        logging.ERROR: logging.Formatter(
        "%(levelname)s %(filename)s:%(lineno)d - %(message)s - %(exc_info)s\n"),
        logging.CRITICAL: logging.Formatter(
        "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n")}
    
    def __init__(self, interface_or_socket, context=None):
        logging.Handler.__init__(self)
        if isinstance(interface_or_socket, zmq.Socket):
            self.socket = interface_or_socket
            self.ctx = self.socket.context
        else:
            self.ctx = context or zmq.Context()
            self.socket = self.ctx.socket(zmq.PUB)
            self.socket.bind(interface_or_socket)

    def format(self,record):
        """Format a record."""
        return self.formatters[record.levelno].format(record)

    def emit(self, record):
        """Emit a log message on my socket."""
        try:
            topic, record.msg = record.msg.split(TOPIC_DELIM,1)
            topic = topic.encode()
        except:
            topic = "".encode()
        try:
            msg = self.format(record).encode()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
        topic_list = []

        if self.root_topic:
            topic_list.append(self.root_topic)

        topic_list.append(record.levelname.encode())

        if topic:
            topic_list.append(topic)

        topic = '.'.encode().join(topic_list)

        # map str, since sometimes we get unicode, and zmq can't deal with it
        self.socket.send_multipart([topic,msg])


class TopicLogger(logging.Logger):
    """A simple wrapper that takes an additional argument to log methods.

    All the regular methods exist, but instead of one msg argument, two
    arguments: topic, msg are passed.

    That is::

        logger.debug('msg')

    Would become::

        logger.debug('topic.sub', 'msg')
    """
    def log(self, level, topic, msg, *args, **kwargs):
        """Log 'msg % args' with level and topic.

        To pass exception information, use the keyword argument exc_info
        with a True value::

            logger.log(level, "zmq.fun", "We have a %s", 
                    "mysterious problem", exc_info=1)
        """
        logging.Logger.log(self, level, '%s::%s'%(topic,msg), *args, **kwargs)

# Generate the methods of TopicLogger, since they are just adding a
# topic prefix to a message.
for name in "debug warn warning error critical fatal".split():
    meth = getattr(logging.Logger,name)
    setattr(TopicLogger, name, 
            lambda self, level, topic, msg, *args, **kwargs: 
                meth(self, level, topic+TOPIC_DELIM+msg,*args, **kwargs))
    
