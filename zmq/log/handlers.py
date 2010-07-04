#!/usr/bin/env python
"""
pyzmq logging module
adapted from StarCluster
http://github.com/jtriley/StarCluster/blob/master/starcluster/logger.py
"""
import logging
from logging import INFO, DEBUG, WARN, ERROR, FATAL

import zmq

class PUBHandler(logging.Handler):
    """A basic log handler that emits log messages
    to a ZMQ PUB socket"""
    root_topic=""
    socket = None
    
    formatters = {      logging.DEBUG: logging.Formatter("%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"),
                        logging.INFO: logging.Formatter("%(message)s\n"),
                        logging.WARN: logging.Formatter("%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"),
                        logging.ERROR: logging.Formatter("%(levelname)s %(filename)s:%(lineno)d - %(message)s - %(exc_info)s\n"),
                        logging.CRITICAL: logging.Formatter("%(levelname)s %(filename)s:%(lineno)d - %(message)s\n")}
    
    def __init__(self, interface):
        logging.Handler.__init__(self)
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.PUB)
        self.socket.bind(interface)
        self.interface = interface

    def format(self,record):
        return self.formatters[record.levelno].format(record)

    def emit(self, record):
        # print record
        # print record.args
        try:
            topic, record.msg = record.msg.split(':',1)
        except:
            topic = ""
        try:
            msg = self.format(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
        # print msg
        if topic:
            msg_tuple = (self.root_topic, topic, record.levelname)
        else:
            msg_tuple = (self.root_topic, record.levelname)
        topic = '.'.join(msg_tuple)
        print topic, msg
        self.socket.send_multipart((topic, msg))

class EnginePUBHanlder(PUBHandler):
    """A simple PUBHandler subclass that sets root_topic"""
    engine=None
    
    def __init__(self, engine, interface):
        PUBHandler.__init__(self,interface)
        self.engine = engine
        
    @property
    def root_topic(self):
        """this is a property, in case the handler is created
        before the engine gets registered with an id"""
        return "engine.%i"%self.engine.id
    
    

# log = logging.getLogger('zmq')
# log.setLevel(logging.DEBUG)
# 
# log.warn('task:whoda')
# log.info('this is a message')

