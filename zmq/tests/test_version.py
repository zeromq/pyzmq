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

from unittest import TestCase
import zmq

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestVersion(TestCase):

    def test_pyzmq_version(self):
        vs = zmq.pyzmq_version()
        vs2 = zmq.__version__
        self.assertTrue(isinstance(vs, str))
        if zmq.__revision__:
            self.assertEquals(vs, '@'.join(vs2, zmq.__revision__))
        else:
            self.assertEquals(vs, vs2)

    def test_pyzmq_version_info(self):
        version = zmq.core.version
        save = version.__version__
        try:
            version.__version__ = '2.10dev'
            info = zmq.pyzmq_version_info()
            self.assertTrue(isinstance(info, tuple))
            self.assertEquals(len(info), 3)
            self.assertTrue(info > (2,10,99))
            self.assertEquals(info, (2,10,float('inf')))
            version.__version__ = '2.1.10'
            info = zmq.pyzmq_version_info()
            self.assertEquals(info, (2,1,10))
            self.assertTrue(info > (2,1,9))
        finally:
            version.__version__ = save

    def test_zmq_version_info(self):
        info = zmq.zmq_version_info()
        self.assertTrue(isinstance(info, tuple))
        self.assertEquals(len(info), 3)
        for item in info:
            self.assertTrue(isinstance(item, int))

    def test_zmq_version(self):
        v = zmq.zmq_version()
        self.assertTrue(isinstance(v, str))

