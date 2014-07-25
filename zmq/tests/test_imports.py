# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import sys
from unittest import TestCase

class TestImports(TestCase):
    """Test Imports - the quickest test to ensure that we haven't
    introduced version-incompatible syntax errors."""
    
    def test_toplevel(self):
        """test toplevel import"""
        import zmq
        
    def test_core(self):
        """test core imports"""
        from zmq import Context
        from zmq import Socket
        from zmq import Poller
        from zmq import Frame
        from zmq import constants
        from zmq import device, proxy
        from zmq import Stopwatch
        from zmq import ( 
            zmq_version,
            zmq_version_info,
            pyzmq_version,
            pyzmq_version_info,
        )
    
    def test_devices(self):
        """test device imports"""
        import zmq.devices
        from zmq.devices import basedevice
        from zmq.devices import monitoredqueue
        from zmq.devices import monitoredqueuedevice
    
    def test_log(self):
        """test log imports"""
        import zmq.log
        from zmq.log import handlers
    
    def test_eventloop(self):
        """test eventloop imports"""
        import zmq.eventloop
        from zmq.eventloop import ioloop
        from zmq.eventloop import zmqstream
        from zmq.eventloop.minitornado.platform import auto
        from zmq.eventloop.minitornado import ioloop
    
    def test_utils(self):
        """test util imports"""
        import zmq.utils
        from zmq.utils import strtypes
        from zmq.utils import jsonapi
    


