"""pyzmq logging handlers.

This mainly defines the PUBHandler object for publishing logging messages over
a zmq.PUB socket.

The PUBHandler can be used with the regular logging module, as in::

    >>> import logging
    >>> handler = PUBHandler('tcp://127.0.0.1:12345')
    >>> handler.root_topic = 'foo'
    >>> logger = logging.getLogger('foobar')
    >>> logger.setLevel(logging.DEBUG)
    >>> logger.addHandler(handler)

After this point, all messages logged by ``logger`` will be published on the
PUB socket.

Code adapted from StarCluster:

    https://github.com/jtriley/StarCluster/blob/StarCluster-0.91/starcluster/logger.py
"""

import logging

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.
from typing import Optional, Union

import zmq

TOPIC_DELIM = "::"  # delimiter for splitting topics on the receiving end.


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

    ctx: zmq.Context
    socket: zmq.Socket

    def __init__(
        self,
        interface_or_socket: Optional[Union[str, zmq.Socket]] = None,
        context: Optional[zmq.Context] = None,
        root_topic: str = '',
        *,
        socket: Optional[zmq.Socket] = None,
        url: Optional[str] = None,
    ) -> None:
        logging.Handler.__init__(self)
        self.root_topic = root_topic
        self.formatters = {
            logging.DEBUG: logging.Formatter(
                "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"
            ),
            logging.INFO: logging.Formatter("%(message)s\n"),
            logging.WARN: logging.Formatter(
                "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"
            ),
            logging.ERROR: logging.Formatter(
                "%(levelname)s %(filename)s:%(lineno)d - %(message)s - %(exc_info)s\n"
            ),
            logging.CRITICAL: logging.Formatter(
                "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"
            ),
        }
        socket_args = [
            arg for arg in (interface_or_socket, socket, url) if arg is not None
        ]
        if len(socket_args) > 1:
            raise ValueError(
                f"Can only specify one of `socket` or `url`, got: {socket_args}"
            )
        if interface_or_socket is not None:
            if isinstance(interface_or_socket, zmq.Socket):
                socket = interface_or_socket
            else:
                url = interface_or_socket
        if socket is not None:
            self.socket = socket
            self.ctx = self.socket.context
        elif url is not None:
            self.ctx = context or zmq.Context()
            self.socket = self.ctx.socket(zmq.PUB)
            self.socket.bind(url)
        else:
            raise ValueError("Please specify a PUB socket or URL.")

    @property
    def root_topic(self) -> str:
        return self._root_topic

    @root_topic.setter
    def root_topic(self, value: str):
        self.setRootTopic(value)

    def setRootTopic(self, root_topic: str):
        """Set the root topic for this handler.

        This value is prepended to all messages published by this handler, and it
        defaults to the empty string ''. When you subscribe to this socket, you must
        set your subscription to an empty string, or to at least the first letter of
        the binary representation of this string to ensure you receive any messages
        from this handler.

        If you use the default empty string root topic, messages will begin with
        the binary representation of the log level string (INFO, WARN, etc.).
        Note that ZMQ SUB sockets can have multiple subscriptions.
        """
        if isinstance(root_topic, bytes):
            root_topic = root_topic.decode("utf8")
        self._root_topic = root_topic

    def setFormatter(self, fmt, level=logging.NOTSET):
        """Set the Formatter for this handler.

        If no level is provided, the same format is used for all levels. This
        will overwrite all selective formatters set in the object constructor.
        """
        if level == logging.NOTSET:
            for fmt_level in self.formatters.keys():
                self.formatters[fmt_level] = fmt
        else:
            self.formatters[level] = fmt

    def format(self, record):
        """Format a record."""
        return self.formatters[record.levelno].format(record)

    def emit(self, record):
        """Emit a log message on my socket."""

        try:
            topic, record.msg = record.msg.split(TOPIC_DELIM, 1)
        except ValueError:
            topic = ""
        try:
            bmsg = self.format(record).encode("utf8")
        except Exception:
            self.handleError(record)
            return

        topic_list = []

        if self.root_topic:
            topic_list.append(self.root_topic)

        topic_list.append(record.levelname)

        if topic:
            topic_list.append(topic)

        btopic = '.'.join(topic_list).encode("utf8")

        self.socket.send_multipart([btopic, bmsg])


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
        logging.Logger.log(self, level, f'{topic}::{msg}', *args, **kwargs)


# Generate the methods of TopicLogger, since they are just adding a
# topic prefix to a message.
for name in "debug warn warning error critical fatal".split():
    meth = getattr(logging.Logger, name)
    setattr(
        TopicLogger,
        name,
        lambda self, level, topic, msg, *args, **kwargs: meth(
            self, level, topic + TOPIC_DELIM + msg, *args, **kwargs
        ),
    )
