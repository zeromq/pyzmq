#
#    Copyright (c) 2012 Brian E. Granger & Min Ragan-Kelley
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

