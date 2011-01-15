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

