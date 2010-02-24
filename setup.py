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

from distutils.core import setup
from distutils.extension import Extension

#-----------------------------------------------------------------------------
# Extensions
#-----------------------------------------------------------------------------

try:
    from Cython.Distutils import build_ext
except ImportError:
    zmq_source = os.path.join('zmq','_zmq.c')
    cmdclass = {}
else:
    zmq_source = os.path.join('zmq','_zmq.pyx')
    cmdclass = {'build_ext': build_ext}

zmq = Extension(
    'zmq._zmq',
    sources = [zmq_source],
    libraries = ['zmq']
)

#-----------------------------------------------------------------------------
# Main setup
#-----------------------------------------------------------------------------

setup(
    name = "pyzmq",
    version = "0.1",
    packages = ['zmq'],
    ext_modules = [zmq],
    author = "Brian E. Granger",
    author_email = "ellisonbg@gmail.com",
    description = "Cython based Python bindings for 0MQ.",
    license = "LGPL",
    cmdclass = cmdclass
)
