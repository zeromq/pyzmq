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

import sys
from unittest import TestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestImports(TestCase):
    """Test Imports - the quickest test to ensure that we haven't
    introduced version-incompatible syntax errors."""
    
    def test_toplevel(self):
        """test toplevel import"""
        import zmq
        
    def test_core(self):
        """test core imports"""
        import zmq.core
        from zmq.core import constants
        from zmq.core import error
        from zmq.core import version
        from zmq.core import context
        from zmq.core import socket
        from zmq.core import message
        from zmq.core import stopwatch
        from zmq.core import device
    
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
        from zmq.eventloop import stack_context
        from zmq.eventloop import ioloop
        from zmq.eventloop import zmqstream
        from zmq.eventloop.platform import auto
    
    def test_utils(self):
        """test util imports"""
        import zmq.utils
        from zmq.utils import strtypes
        from zmq.utils import jsonapi
    



