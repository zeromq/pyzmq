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
logging would be to broadcast log messages over a PUB socket, so we have provided a
:class:`.PUBHandler` class for doing just that.

You can use PyZMQ as a log handler with no previous knowledge of how ZMQ works, 
and without writing any ZMQ-specific code in your Python project.

Getting Started
---------------
Ensure you have installed the pyzmq package from pip, ideally in a 
`virtual environment <https://docs.python.org/3/library/venv.html>`_ 
you created for your project::

    pip install pyzmq

Next, configure logging in your Python module and setup the ZMQ log handler::

    import logging
    from zmq.log.handlers import PUBHandler

    zmq_log_handler = PUBHandler('tcp://127.0.0.1:12345')
    logger = logging.getLogger()
    logger.addHandler(zmq_log_handler)

Usually, you will add the handler only once in the top-level module of your
project, on the root logger, just as we did here.

You can choose any IP address and port number that works on your system. We 
used ``tcp://127.0.0.1:12345`` to broadcast events via TCP on the localhost
interface at port 12345. Make note of what you choose here as you will need it
later when you listen to the events.

Logging messages works exactly like normal. This will send an INFO-level
message on the logger we configured above, and that message will be
published on a ZMQ PUB/SUB socket::

    logger.info('hello world!')

You can use this module's built-in command line interface to "tune in" to
messages broadcast by the  log handler. To start the log watcher,
run this command from a shell that has access to the pyzmq package
(usually a virtual environment)::

    python -m zmq.log tcp://127.0.0.1:12345

Then, in a separate process, run your Python module that emits log
messages. You should see them appear almost immediately.

Using the Log Watcher
*********************
The included log watcher command line utility is helpful not only for
viewing messages, but also a programming guide to build your own ZMQ
subscriber for log messages.

To see what options are available, pass the ``--help`` parameter::

    python -m zmq.log --help

The log watcher includes features to add a timestamp to the messages,
align the messages across different error levels, and even colorize
the output based on error level.



Slow Joiner Problem
*******************
The great thing about using ZMQ sockets is that you can start the publisher
and subscribers in any order, and you can start & stop any of them while
you leave the others running. 

When using ZMQ for logging, this means you
can leave the log watcher running while you start & stop your main
Python module.

However, you need to be aware of what the ZMQ project calls the
`"slow joiner problem" <http://zguide.zeromq.org/page:all#Getting-the-Message-Out>`_ . 
To oversimplify, it means it can take a bit of
time for subscribers to re-connect to a publisher that has just
started up again. If the publisher starts and immediately sends a
message, subscribers will likely miss it.

The simplistic workaround when using PyZMQ for logging is to ``sleep()`` 
briefly after startup, before sending any log messages. See the complete
example below for more details.


Custom Log Formats
******************
A common Python logging recipe encourages 
`use of the current module name
<https://docs.python.org/howto/logging-cookbook.html#using-logging-in-multiple-modules>`_
as the name of the logger. This allows your log messages to reflect your
code hierarchy in a larger project with minimal configuration.

You will need to set a different formatter to see these names in your
ZMQ-published logs. The setFormatter() method accepts a logging.Formatter
instance and optionally a log level to apply the handler to. For example::

    zmq_log_handler = PUBHandler('tcp://127.0.0.1:12345')
    zmq_log_handler.setFormatter(logging.Formatter(fmt='{name} > {message}', style='{'))
    zmq_log_handler.setFormatter(logging.Formatter(fmt='{name} #{lineno:>3} > {message}', style='{'), logging.DEBUG)


Root Topic
**********
By default, the PUBHandler and log watcher use the empty string as the
root topic for published messages. This works well out-of-the-box, but you can
easily set a different root topic string to take advantage of ZMQ's built-in
topic filtering mechanism.

First, set the root topic on the handler:

    zmq_log_handler = PUBHandler('tcp://127.0.0.1:12345')
    zmq_log_handler.setRootTopic('custom_topic')

Then specify that topic when you start the log watcher:

    python -m zmq.log -t custom_topic tcp://127.0.0.1:12345


Complete example
****************
Assuming this project hierarchy:

    example.py
      greetings
        hello.py

If you have this in ``example.py``::

    import logging
    from time import sleep
    from zmq.log.handlers import PUBHandler

    from greetings import hello

    zmq_log_handler = PUBHandler('tcp://127.0.0.1:12345')
    zmq_log_handler.setFormatter(logging.Formatter(fmt='{name} > {message}', style='{'))
    zmq_log_handler.setFormatter(logging.Formatter(fmt='{name} #{lineno:>3} > {message}', style='{'), logging.DEBUG)
    zmq_log_handler.setRootTopic('greeter')

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(zmq_log_handler)

    if __name__ == '__main__':
        sleep(0.1)
        msg_count = 5
        logger.warning('Preparing to greet the world...')
        for i in range(1,msg_count+1):
            logger.debug('Sending message {} of {}'.format(i,msg_count))
            hello.world()
            sleep(1.0)
        logger.info('Done!')

And this in ``hello.py``::

    import logging

    logger = logging.getLogger(__name__)

    def world():
        logger.info('hello world!')

You can start a log watcher in one process::

    python -m zmq.log -t greeter --align tcp://127.0.0.1:12345

And then run ``example.py`` in another process::

    python example.py

You should see the following output from the log watcher::

    greeter.WARNING | root > Preparing to greet the world...
    greeter.DEBUG   | root # 21 > Sending message 1 of 5
    greeter.INFO    | greetings.hello > hello world!
    greeter.DEBUG   | root # 21 > Sending message 2 of 5
    greeter.INFO    | greetings.hello > hello world!
    greeter.DEBUG   | root # 21 > Sending message 3 of 5
    greeter.INFO    | greetings.hello > hello world!
    greeter.DEBUG   | root # 21 > Sending message 4 of 5
    greeter.INFO    | greetings.hello > hello world!
    greeter.DEBUG   | root # 21 > Sending message 5 of 5
    greeter.INFO    | greetings.hello > hello world!
    greeter.INFO    | root > Done!




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
