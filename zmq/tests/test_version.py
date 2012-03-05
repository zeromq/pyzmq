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

