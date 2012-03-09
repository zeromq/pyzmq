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

import zmq
from zmq.tests import BaseZMQTestCase, SkipTest


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


class TestZMQWeb(BaseZMQTestCase):
    
    def setUp(self):
        try:
            import tornado
        except ImportError:
            raise SkipTest("zmq.web requires tornado")
        
        BaseZMQTestCase.setUp(self)
    
    def test_imports(self):
        """zmq.web is importable"""
        from zmq import web

