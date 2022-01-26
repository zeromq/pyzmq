# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import os
from unittest import TestCase

import zmq


class TestIncludes(TestCase):
    def test_get_includes(self):
        from os.path import basename, dirname

        includes = zmq.get_includes()
        self.assertIsInstance(includes, list)
        self.assertGreaterEqual(len(includes), 2)
        parent = includes[0]
        self.assertIsInstance(parent, str)
        utilsdir = includes[1]
        self.assertIsInstance(utilsdir, str)
        utils = basename(utilsdir)
        self.assertEqual(utils, "utils")

    def test_get_library_dirs(self):
        from os.path import basename, dirname

        libdirs = zmq.get_library_dirs()
        self.assertIsInstance(libdirs, list)
        self.assertEqual(len(libdirs), 1)
        parent = libdirs[0]
        self.assertIsInstance(parent, str)
        libdir = basename(parent)
        self.assertEqual(libdir, "zmq")
