#!/usr/bin/env python

#
#    Copyright (c) 2010 Brian E. Granger
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

import os, sys

from distutils.core import setup, Command
from distutils.extension import Extension

from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin, walk


#-----------------------------------------------------------------------------
# Extra commands
#-----------------------------------------------------------------------------

class TestCommand(Command):
    """Custom distutils command to run the test suite."""

    user_options = [ ]

    def initialize_options(self):
        self._dir = os.getcwd()

    def finalize_options(self):
        pass

    def run(self):
        """Finds all the tests modules in zmq/tests/, and runs them."""
        testfiles = [ ]
        for t in glob(pjoin(self._dir, 'zmq', 'tests', '*.py')):
            if not t.endswith('__init__.py'):
                testfiles.append('.'.join(
                    ['zmq.tests', splitext(basename(t))[0]])
                )
        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = 1)
        t.run(tests)


class CleanCommand(Command):
    """Custom distutils command to clean the .so and .pyc files."""

    user_options = [ ]

    def initialize_options(self):
        self._clean_me = [pjoin('zmq', '_zmq.so') ]
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.pyc'):
                    self._clean_me.append(pjoin(root, f))

    def finalize_options(self):
        pass

    def run(self):
        for clean_me in self._clean_me:
            try:
                os.unlink(clean_me)
            except:
                pass

#-----------------------------------------------------------------------------
# Extensions
#-----------------------------------------------------------------------------

cmdclass = {'test':TestCommand, 'clean':CleanCommand }

try:
    from Cython.Distutils import build_ext
except ImportError:
    zmq_source = os.path.join('zmq','_zmq.c')
else:
    zmq_source = os.path.join('zmq','_zmq.pyx')
    cmdclass['build_ext'] =  build_ext

if sys.platform == 'win32':
    libzmq = 'libzmq'
else:
    libzmq = 'zmq'

zmq = Extension(
    'zmq._zmq',
    sources = [zmq_source],
    libraries = [libzmq]
)

#-----------------------------------------------------------------------------
# Main setup
#-----------------------------------------------------------------------------

setup(
    name = "pyzmq",
    version = "2.0.7",
    packages = ['zmq', 'zmq.tests', 'zmq.eventloop'],
    ext_modules = [zmq],
    author = "Brian E. Granger",
    author_email = "ellisonbg@gmail.com",
    description = "Cython based Python bindings for 0MQ.",
    license = "LGPL",
    cmdclass = cmdclass
)

