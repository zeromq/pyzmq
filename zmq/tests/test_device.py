#-----------------------------------------------------------------------------
#  Copyright (c) 2010-2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import time

import zmq
from zmq import devices
from zmq.tests import BaseZMQTestCase, SkipTest
from zmq.utils.strtypes import (bytes,unicode,basestring)

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
devices.ThreadDevice.context_factory = zmq.Context

class TestDevice(BaseZMQTestCase):
    
    def test_device_types(self):
        for devtype in (zmq.STREAMER, zmq.FORWARDER, zmq.QUEUE):
            dev = devices.Device(devtype, zmq.PAIR, zmq.PAIR)
            self.assertEquals(dev.device_type, devtype)
            del dev
    
    def test_device_attributes(self):
        dev = devices.Device(zmq.QUEUE, zmq.SUB, zmq.PUB)
        self.assertEquals(dev.in_type, zmq.SUB)
        self.assertEquals(dev.out_type, zmq.PUB)
        self.assertEquals(dev.device_type, zmq.QUEUE)
        self.assertEquals(dev.daemon, True)
        del dev
    
    def test_tsdevice_attributes(self):
        dev = devices.Device(zmq.QUEUE, zmq.SUB, zmq.PUB)
        self.assertEquals(dev.in_type, zmq.SUB)
        self.assertEquals(dev.out_type, zmq.PUB)
        self.assertEquals(dev.device_type, zmq.QUEUE)
        self.assertEquals(dev.daemon, True)
        del dev
        
    
    def test_single_socket_forwarder_connect(self):
        dev = devices.ThreadDevice(zmq.QUEUE, zmq.REP, -1)
        req = self.context.socket(zmq.REQ)
        port = req.bind_to_random_port('tcp://127.0.0.1')
        dev.connect_in('tcp://127.0.0.1:%i'%port)
        dev.start()
        time.sleep(.25)
        msg = b'hello'
        req.send(msg)
        self.assertEquals(msg, self.recv(req))
        del dev
        req.close()
        dev = devices.ThreadDevice(zmq.QUEUE, zmq.REP, -1)
        req = self.context.socket(zmq.REQ)
        port = req.bind_to_random_port('tcp://127.0.0.1')
        dev.connect_out('tcp://127.0.0.1:%i'%port)
        dev.start()
        time.sleep(.25)
        msg = b'hello again'
        req.send(msg)
        self.assertEquals(msg, self.recv(req))
        del dev
        req.close()
        
    def test_single_socket_forwarder_bind(self):
        dev = devices.ThreadDevice(zmq.QUEUE, zmq.REP, -1)
        # select random port:
        binder = self.context.socket(zmq.REQ)
        port = binder.bind_to_random_port('tcp://127.0.0.1')
        binder.close()
        time.sleep(0.1)
        req = self.context.socket(zmq.REQ)
        req.connect('tcp://127.0.0.1:%i'%port)
        dev.bind_in('tcp://127.0.0.1:%i'%port)
        dev.start()
        time.sleep(.25)
        msg = b'hello'
        req.send(msg)
        self.assertEquals(msg, self.recv(req))
        del dev
        req.close()
        dev = devices.ThreadDevice(zmq.QUEUE, zmq.REP, -1)
        # select random port:
        binder = self.context.socket(zmq.REQ)
        port = binder.bind_to_random_port('tcp://127.0.0.1')
        binder.close()
        time.sleep(0.1)
        req = self.context.socket(zmq.REQ)
        req.connect('tcp://127.0.0.1:%i'%port)
        dev.bind_in('tcp://127.0.0.1:%i'%port)
        dev.start()
        time.sleep(.25)
        msg = b'hello again'
        req.send(msg)
        self.assertEquals(msg, self.recv(req))
        del dev
        req.close()

