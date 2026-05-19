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

Or using ``dictConfig``, as in::

    >>> from logging.config import dictConfig
    >>> socket = Context.instance().socket(PUB)
    >>> socket.connect('tcp://127.0.0.1:12345')
    >>> dictConfig({
    >>>     'version': 1,
    >>>     'handlers': {
    >>>         'zmq': {
    >>>             'class': 'zmq.log.handlers.PUBHandler',
    >>>             'level': logging.DEBUG,
    >>>             'root_topic': 'foo',
    >>>             'interface_or_socket': socket
    >>>         }
    >>>     },
    >>>     'root': {
    >>>         'level': 'DEBUG',
    >>>         'handlers': ['zmq'],
    >>>     }
    >>> })


After this point, all messages logged by ``logger`` will be published on the
PUB socket.

Code adapted from StarCluster:

    https://github.com/jtriley/StarCluster/blob/StarCluster-0.91/starcluster/logger.py
"""

from __future__ import annotations

import logging
from copy import copy
from typing import TYPE_CHECKING, Any, Final, cast

import zmq

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import TracebackType
    from typing import type_check_only

    from typing_extensions import TypeAlias, TypedDict, Unpack

    # these aliases are based on the `logging` typeshed stdlib stubs
    _SysExcInfo: TypeAlias = (
        tuple[type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None]
    )
    _ExcInfo: TypeAlias = bool | _SysExcInfo | BaseException

    @type_check_only
    class _LogKwargs(TypedDict):
        exc_info: _ExcInfo | None
        stack_info: bool
        stacklevel: int
        extra: Mapping[str, object]

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


TOPIC_DELIM: Final = "::"  # delimiter for splitting topics on the receiving end.


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

    formatters: dict[int, logging.Formatter | None]
    ctx: zmq.Context
    socket: zmq.Socket

    def __init__(
        self,
        interface_or_socket: str | zmq.Socket,
        context: zmq.Context | None = None,
        root_topic: str = '',
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
        if isinstance(interface_or_socket, zmq.Socket):
            self.socket = interface_or_socket
            self.ctx = self.socket.context
        else:
            self.ctx = context or zmq.Context()
            self.socket = self.ctx.socket(zmq.PUB)
            self.socket.bind(interface_or_socket)

    @property
    def root_topic(self) -> str:
        return self._root_topic

    @root_topic.setter
    def root_topic(self, value: str) -> None:
        self.setRootTopic(value)

    def setRootTopic(self, root_topic: str) -> None:
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

    def setFormatter(
        self,
        fmt: logging.Formatter | None,
        level: int = logging.NOTSET,
    ) -> None:
        """Set the Formatter for this handler.

        If no level is provided, the same format is used for all levels. This
        will overwrite all selective formatters set in the object constructor.
        """
        if level == logging.NOTSET:
            for fmt_level in self.formatters.keys():
                self.formatters[fmt_level] = fmt
        else:
            self.formatters[level] = fmt

    def format(self, record: logging.LogRecord) -> str:
        """Format a record."""
        return cast("logging.Formatter", self.formatters[record.levelno]).format(record)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log message on my socket."""

        # LogRecord.getMessage explicitly allows msg to be anything _castable_ to a str
        try:
            topic, msg = str(record.msg).split(TOPIC_DELIM, 1)
        except ValueError:
            topic = ""
        else:
            # copy to avoid mutating LogRecord in-place
            record = copy(record)
            record.msg = msg

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

        btopic = '.'.join(topic_list).encode("utf8", "replace")

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

    def log(  # type:ignore[override]
        self, level: int, topic: str, msg: str, *args: Any, **kwargs: Unpack[_LogKwargs]
    ) -> None:
        """Log 'msg % args' with level and topic.

        To pass exception information, use the keyword argument exc_info
        with a True value::

            logger.log(level, "zmq.fun", "We have a %s",
                    "mysterious problem", exc_info=1)
        """
        logging.Logger.log(self, level, f'{topic}{TOPIC_DELIM}{msg}', *args, **kwargs)

    if TYPE_CHECKING:

        def debug(  # type:ignore[override]
            self, topic: str, msg: str, *args: Any, **kwargs: Unpack[_LogKwargs]
        ) -> None: ...
        def warn(  # type:ignore[override]
            self, topic: str, msg: str, *args: Any, **kwargs: Unpack[_LogKwargs]
        ) -> None: ...
        def warning(  # type:ignore[override]
            self, topic: str, msg: str, *args: Any, **kwargs: Unpack[_LogKwargs]
        ) -> None: ...
        def error(  # type:ignore[override]
            self, topic: str, msg: str, *args: Any, **kwargs: Unpack[_LogKwargs]
        ) -> None: ...
        def critical(  # type:ignore[override]
            self, topic: str, msg: str, *args: Any, **kwargs: Unpack[_LogKwargs]
        ) -> None: ...
        def fatal(  # type:ignore[override]
            self, topic: str, msg: str, *args: Any, **kwargs: Unpack[_LogKwargs]
        ) -> None: ...


# Generate the methods of TopicLogger, since they are just adding a
# topic prefix to a message.
for name in "debug warn warning error critical fatal".split():
    try:
        meth = getattr(logging.Logger, name)
    except AttributeError:
        # some methods are missing, e.g. Logger.warn was removed from Python 3.13
        continue
    setattr(
        TopicLogger,
        name,
        lambda self, level, topic, msg, *args, **kwargs: meth(
            self, level, topic + TOPIC_DELIM + msg, *args, **kwargs
        ),
    )
