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

try:
    from zmq import devices
    devices.ThreadDevice.context_factory = zmq.Context
except:
    devices = False


from zmq.tests import BaseZMQTestCase, SkipTest, have_gevent, GreenTest, \
                      skipIf
from zmq.utils.strtypes import (bytes,unicode,basestring)

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestDevice(BaseZMQTestCase):
    @skipIf(not devices, "zmq.devices not available")
    def test_device_types(self):
        for devtype in (zmq.STREAMER, zmq.FORWARDER, zmq.QUEUE):
            dev = devices.Device(devtype, zmq.PAIR, zmq.PAIR)
            self.assertEquals(dev.device_type, devtype)
            del dev

    @skipIf(not devices, "zmq.devices not available")
    def test_device_attributes(self):
        dev = devices.Device(zmq.QUEUE, zmq.SUB, zmq.PUB)
        self.assertEquals(dev.in_type, zmq.SUB)
        self.assertEquals(dev.out_type, zmq.PUB)
        self.assertEquals(dev.device_type, zmq.QUEUE)
        self.assertEquals(dev.daemon, True)
        del dev

    @skipIf(not devices, "zmq.devices not available")
    def test_tsdevice_attributes(self):
        dev = devices.Device(zmq.QUEUE, zmq.SUB, zmq.PUB)
        self.assertEquals(dev.in_type, zmq.SUB)
        self.assertEquals(dev.out_type, zmq.PUB)
        self.assertEquals(dev.device_type, zmq.QUEUE)
        self.assertEquals(dev.daemon, True)
        del dev


    @skipIf(not devices, "zmq.devices not available")
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

    @skipIf(not devices, "zmq.devices not available")
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

if have_gevent:
    import gevent
    import zmq.green
    
    class TestDeviceGreen(GreenTest, BaseZMQTestCase):
        
        def test_green_device(self):
            rep = self.context.socket(zmq.REP)
            req = self.context.socket(zmq.REQ)
            self.sockets.extend([req, rep])
            port = rep.bind_to_random_port('tcp://127.0.0.1')
            g = gevent.spawn(zmq.green.device, zmq.QUEUE, rep, rep)
            req.connect('tcp://127.0.0.1:%i' % port)
            req.send(b'hi')
            timeout = gevent.Timeout(1)
            timeout.start()
            receiver = gevent.spawn(req.recv)
            self.assertEqual(receiver.get(1), b'hi')
            timeout.cancel()
            g.kill()
            
