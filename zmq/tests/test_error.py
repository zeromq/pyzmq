# -*- coding: utf8 -*-
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
import time

from unittest import TestCase

from zmq import ZMQError, strerror

if sys.version_info[0] >= 3:
    long = int

class TestZMQError(TestCase):
    
    def test_strerror(self):
        """test that strerror gets the right type."""
        for i in range(10):
            e = strerror(i)
            self.assertTrue(isinstance(e, str))
    
    def test_zmqerror(self):
        for errno in range(10):
            e = ZMQError(errno)
            self.assertEquals(e.errno, errno)
            self.assertEquals(str(e), strerror(errno))

