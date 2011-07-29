.. PyZMQ logging doc, by Min Ragan-Kelley, 2011

.. _logging:

Asynchronous Logging via PyZMQ
==============================

.. seealso::

    * The ØMQ guide `coverage <http://zguide.zeromq.org/chapter:all#toc7>`_ of PUB/SUB
      messaging
    * Python logging module `documentation <http://docs.python.org/library/logging.html>`_

Python provides extensible logging facilities through its :py:mod:`logging` module. This
module allows for easily extensible logging functionality through the use of
:py:class:`~logging.Handler` objects. The most obvious case for hooking up pyzmq to
logging would be to broadcast log messages over a PUB socket, so we have provides a
:class:`.PUBHandler` class for doing just that.

PUB/SUB and Topics
------------------

The ØMQ PUB/SUB pattern consists of a PUB socket broadcasting messages, and a collection
of SUB sockets that receive those messages. Each PUB message is a multipart-message, where
the first part is interpreted as a topic. SUB sockets can subscribe to topics by setting
their ``SUBSCRIBE`` sockopt, e.g.::

    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.SUBSCRIBE, 'topic1')
    sub.setsockopt(zmq.SUBSCRIBE, 'topic2')

When subscribed, the SUB socket will only receive messages where the first part *starts
with* one of the topics set via ``SUBSCRIBE``. The default behavior is to exclude all
messages, and subscribing to the empty string '' will receive all messages.

PUBHandler
----------

The :class:`.PUBHandler` object is created for allowing the python logging to be emitted
on a PUB socket. The main difference between a PUBHandler and a regular logging Handler is
the inclusion of topics. For the most basic logging, you can simply create a PUBHandler
with an interface or a configured PUB socket, and just let it go::

    pub = context.socket(zmq.PUB)
    pub.bind('tcp://*:12345')
    handler = PUBHandler(pub)
    logger = logging.getLogger()
    logger.addHandler(handler)

At this point, all messages logged with the default logger will be broadcast on the pub
socket.

the PUBHandler does work with topics, and the handler has an attribute ``root_topic``::

    handler.root_topic = 'myprogram'

Python loggers also have loglevels. The base topic of messages emitted by the PUBHandler
will be of the form: ``<handler.root_topic>.<loglevel>``, e.g. 'myprogram.INFO' or
'whatever.ERROR'. This way, subscribers can easily subscribe to subsets of the logging
messages. Log messages are always two-part, where the first part is the topic tree, and
the second part is the actual log message.

    >>> logger.info('hello there')
    >>> print sub.recv_multipart()
    ['myprogram.INFO', 'hello there']

Subtopics
*********

You can also add to the topic tree below the loglevel on an individual message basis.
Assuming your logger is connected to a PUBHandler, you can add as many additional topics
on the front of the message, which will be added always after the loglevel. A special
delimiter defined at ``zmq.log.handlers.TOPIC_DELIM`` is scanned by the PUBHandler, so if
you pass your own subtopics prior to that symbol, they will be stripped from the message
and added to the topic tree::

    >>> log_msg  = "hello there"
    >>> subtopic = "sub.topic"
    >>> msg = zmq.log.handlers.TOPIC_DELIM.join([subtopic, log_msg])
    >>> logger.warn(msg)
    >>> print sub.recv_multipart()
    ['myprogram.WARN.sub.topic', 'hello there']


