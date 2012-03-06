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

from zmq import Stopwatch, ZMQError

if sys.version_info[0] >= 3:
    long = int

class TestStopWatch(TestCase):
    
    def test_stop_long(self):
        """Ensure stop returns a long int."""
        watch = Stopwatch()
        watch.start()
        us = watch.stop()
        self.assertTrue(isinstance(us, long))
        
    def test_stop_microseconds(self):
        """Test that stop/sleep have right units."""
        watch = Stopwatch()
        watch.start()
        tic = time.time()
        watch.sleep(1)
        us = watch.stop()
        toc = time.time()
        self.assertAlmostEqual(us/1e6,(toc-tic),places=0)
    
    def test_double_stop(self):
        """Test error raised on multiple calls to stop."""
        watch = Stopwatch()
        watch.start()
        watch.stop()
        self.assertRaises(ZMQError, watch.stop)
        self.assertRaises(ZMQError, watch.stop)
    
