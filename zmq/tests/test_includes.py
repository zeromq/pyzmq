# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import os
from unittest import TestCase

import zmq


class TestIncludes(TestCase):
    def test_get_includes(self):
        from os.path import basename, dirname

        includes = zmq.get_includes()
        self.assertTrue(isinstance(includes, list))
        self.assertTrue(len(includes) >= 2)
        parent = includes[0]
        self.assertTrue(isinstance(parent, str))
        utilsdir = includes[1]
        self.assertTrue(isinstance(utilsdir, str))
        utils = basename(utilsdir)
        self.assertEqual(utils, "utils")

    def test_get_library_dirs(self):
        from os.path import basename, dirname

        libdirs = zmq.get_library_dirs()
        self.assertTrue(isinstance(libdirs, list))
        self.assertEqual(len(libdirs), 1)
        parent = libdirs[0]
        self.assertTrue(isinstance(parent, str))
        libdir = basename(parent)
        self.assertEqual(libdir, "zmq")
