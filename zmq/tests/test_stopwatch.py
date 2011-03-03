#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#    Copyright (c) 2011 Min Ragan-Kelley
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
    
