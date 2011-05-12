#
#    Copyright (c) 2010 Brian E. Granger
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
import time
from unittest import TestCase

import zmq
from zmq.log import handlers
from zmq.utils.strtypes import asbytes
from zmq.tests import BaseZMQTestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestPubLog(BaseZMQTestCase):
    
    iface = 'inproc://zmqlog'
    topic= asbytes('zmq')
    
    @property
    def logger(self):
        # print dir(self)
        logger = logging.getLogger('zmqtest')
        logger.setLevel(logging.DEBUG)
        return logger
    
    def connect_handler(self):
        logger = self.logger
        pub,sub = self.create_bound_pair(zmq.PUB, zmq.SUB)
        handler = handlers.PUBHandler(pub)
        handler.setLevel(logging.DEBUG)
        handler.root_topic = self.topic
        logger.addHandler(handler)
        sub.setsockopt(zmq.SUBSCRIBE, self.topic)
        time.sleep(0.1)
        return logger, handler, sub
    
    def test_init_iface(self):
        logger = self.logger
        ctx = self.context
        handler = handlers.PUBHandler(self.iface)
        self.assertFalse(handler.ctx is ctx)
        self.sockets.append(handler.socket)
        # handler.ctx.term()
        handler = handlers.PUBHandler(self.iface, self.context)
        self.sockets.append(handler.socket)
        self.assertTrue(handler.ctx is ctx)
        handler.setLevel(logging.DEBUG)
        handler.root_topic = self.topic
        logger.addHandler(handler)
        sub = ctx.socket(zmq.SUB)
        self.sockets.append(sub)
        sub.setsockopt(zmq.SUBSCRIBE, self.topic)
        sub.connect(self.iface)
        import time; time.sleep(0.25)
        msg1 = 'message'
        logger.info(msg1)
        
        (topic, msg2) = sub.recv_multipart()
        self.assertEquals(topic, asbytes('zmq.INFO'))
        self.assertEquals(msg2, asbytes(msg1+'\n'))
        logger.removeHandler(handler)
    
    def test_init_socket(self):
        pub,sub = self.create_bound_pair(zmq.PUB, zmq.SUB)
        logger = self.logger
        handler = handlers.PUBHandler(pub)
        handler.setLevel(logging.DEBUG)
        handler.root_topic = self.topic
        logger.addHandler(handler)
        
        self.assertTrue(handler.socket is pub)
        self.assertTrue(handler.ctx is pub.context)
        self.assertTrue(handler.ctx is self.context)
        sub.setsockopt(zmq.SUBSCRIBE, self.topic)
        import time; time.sleep(0.1)
        msg1 = 'message'
        logger.info(msg1)
        
        (topic, msg2) = sub.recv_multipart()
        self.assertEquals(topic, asbytes('zmq.INFO'))
        self.assertEquals(msg2, asbytes(msg1+'\n'))
        logger.removeHandler(handler)
    
    def test_root_topic(self):
        logger, handler, sub = self.connect_handler()
        handler.socket.bind(self.iface)
        sub2 = sub.context.socket(zmq.SUB)
        self.sockets.append(sub2)
        sub2.connect(self.iface)
        sub2.setsockopt(zmq.SUBSCRIBE, asbytes(''))
        handler.root_topic = asbytes('twoonly')
        msg1 = 'ignored'
        logger.info(msg1)
        self.assertRaisesErrno(zmq.EAGAIN, sub.recv, zmq.NOBLOCK)
        topic,msg2 = sub2.recv_multipart()
        self.assertEquals(topic, asbytes('twoonly.INFO'))
        self.assertEquals(msg2, asbytes(msg1+'\n'))
        
        
        
        logger.removeHandler(handler)

