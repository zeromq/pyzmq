#!/usr/bin/env python
"""
pyzmq logging module
This mainly defines the PUBHandler object for 
adapted from StarCluster
http://github.com/jtriley/StarCluster/blob/master/starcluster/logger.py
"""
import logging
from logging import INFO, DEBUG, WARN, ERROR, FATAL

import zmq

TOPIC_DELIM="::"

class PUBHandler(logging.Handler):
    """A basic logging handler that emits log messages
    through a ZMQ PUB socket.
    Takes a PUB socket already bound to interfaces or an interface to bind to.
    >>> sock = context.socket(zmq.PUB)
    >>> sock.bind('inproc://log')
    >>> handler = PUBHandler(sock)
    OR
    >>> handler = PUBHandler('inproc://loc')
    these are equivalent.
    
    log messages handled by this handler are broadcast with ZMQ topics
    this.root_topic comes first, followed by the log level (DEBUG,INFO,etc.),
    followed by any additional subtopics specified in the message by:
    log.debug("subtopic.subsub::the real message")
    
    """
    root_topic=""
    socket = None
    
    formatters = {      logging.DEBUG: logging.Formatter("%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"),
                        logging.INFO: logging.Formatter("%(message)s\n"),
                        logging.WARN: logging.Formatter("%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"),
                        logging.ERROR: logging.Formatter("%(levelname)s %(filename)s:%(lineno)d - %(message)s - %(exc_info)s\n"),
                        logging.CRITICAL: logging.Formatter("%(levelname)s %(filename)s:%(lineno)d - %(message)s\n")}
    
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
        return self.formatters[record.levelno].format(record)

    def emit(self, record):
        # print record
        # print record.args
        try:
            topic, record.msg = record.msg.split(TOPIC_DELIM,1)
        except:
            topic = ""
        try:
            msg = self.format(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
        # print msg
        topic_list = []
        
        if self.root_topic:
            topic_list.append(self.root_topic)
        
        topic_list.append(record.levelname)
        
        if topic:
            topic_list.append(topic)
        
        topic = '.'.join(topic_list)
        # print topic, msg
        # map str, since sometimes we get unicode, and zmq can't deal with it
        self.socket.send_multipart(map(str, (topic, msg)))

class TopicLogger(logging.Logger):
    """a simple wrapper that takes an additional argument to log methods
    All the regular methods exist, but instead of one msg argument, two arguments topic,msg are passed
    i.e. logger.debug('msg') would become: logger.debug('topic.sub', 'msg')"""
    
    def log(self, level, topic, msg, *args, **kwargs):
        """    Log 'msg % args' with the integer severity 'level'.
            and ZMQ PUB topic 'topic'
            
            To pass exception information, use the keyword argument exc_info with
            a true value, e.g.

            logger.log(level, "zmq.fun", "We have a %s", "mysterious problem", exc_info=1)
        """
        logging.Logger.log(self, level, '%s::%s'%(topic,msg), *args, **kwargs)

for name in "debug warn warning error critical fatal".split():
    meth = getattr(logging.Logger,name)
    setattr(TopicLogger, name, 
            lambda self, level, topic, msg, *args, **kwargs: 
                meth(self, level, topic+TOPIC_DELIM+msg,*args, **kwargs))
    
