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
from distutils.ccompiler import get_default_compiler
from distutils.extension import Extension
from distutils.command.sdist import sdist
from distutils.command.build_ext import build_ext

from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin

try:
    from os.path import walk
except:
    from os import walk

#-----------------------------------------------------------------------------
# Flags
#-----------------------------------------------------------------------------
# ignore unused-function and strict-aliasing warnings, of which there
# will be many from the Cython generated code:
# note that this is only for gcc-style compilers
if get_default_compiler() in ('unix', 'mingw32'):
    ignore_common_warnings=True
else:
    ignore_common_warnings=True

release = False # flag for whether to include *.c in package_data

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
        t = TextTestRunner(verbosity = 2)
        t.run(tests)


class CleanCommand(Command):
    """Custom distutils command to clean the .so and .pyc files."""

    user_options = [ ]

    def initialize_options(self):
        self._clean_me = []
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.pyc') or f.endswith('.so'):
                    self._clean_me.append(pjoin(root, f))

    def finalize_options(self):
        pass

    def run(self):
        for clean_me in self._clean_me:
            try:
                os.unlink(clean_me)
            except:
                pass


class CheckSDist(sdist):
    """Custom sdist that ensures Cython has compiled all pyx files to c."""

    def initialize_options(self):
        sdist.initialize_options(self)
        self._pyxfiles = []
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.pyx'):
                    self._pyxfiles.append(pjoin(root, f))
    def run(self):
        for pyxfile in self._pyxfiles:
            cfile = pyxfile[:-3]+'c'
            msg = "C-source file '%s' not found."%(cfile)+\
            " Run 'setup.py cython' before sdist."
            assert os.path.isfile(cfile), msg
        sdist.run(self)

class CheckingBuildExt(build_ext):
    """Subclass build_ext to get clearer report if Cython is neccessary."""
    
    def check_cython_extensions(self, extensions):
        for ext in extensions:
          for src in ext.sources:
            if not os.path.exists(src):
                raise IOError('',
                """Cython-generated file '%s' not found.
                Cython is required to compile pyzmq from a development branch.
                Please install Cython or download a release package of pyzmq.
                """%src)
    def build_extensions(self):
        self.check_cython_extensions(self.extensions)
        self.check_extensions_list(self.extensions)

        for ext in self.extensions:
            self.build_extension(ext)

#-----------------------------------------------------------------------------
# Suppress Common warnings
#-----------------------------------------------------------------------------

extra_flags = []
if ignore_common_warnings:
    for warning in ('unused-function', 'strict-aliasing'):
        extra_flags.append('-Wno-'+warning)

#-----------------------------------------------------------------------------
# Extensions
#-----------------------------------------------------------------------------

cmdclass = {'test':TestCommand, 'clean':CleanCommand }

includes = [pjoin('zmq', sub) for sub in ('utils','core','devices')]

def pxd(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.pxd'))

def pyx(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.pyx'))

def dotc(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.c'))

czmq = pxd('core', 'czmq')
allocate = pxd('utils', 'allocate')
buffers = pxd('utils', 'buffers')

submodules = dict(
    core = {'constants': [czmq],
            'error':[czmq],
            'poll':[czmq, allocate], 
            'stopwatch':[czmq],
            'context':[pxd('core', 'socket'), czmq],
            'message':[czmq, buffers],
            'socket':[pxd('core', 'context'), pxd('core', 'message'), 
                      czmq, allocate, buffers],
            'device':[czmq],
            'version':[czmq],
    },
    crypto = {'encryptedsocket':[pxd('core', 'socket'), czmq, buffers],
    },
    devices = {
            'monitoredqueue':[pxd('devices', 'basedevice'), buffers, czmq],
    },
    utils = {
            'initthreads':[czmq]
    }
)

try:
    from Cython.Distutils import build_ext
except ImportError:
    suffix = '.c'
    cmdclass['build_ext'] = CheckingBuildExt
else:
    
    suffix = '.pyx'
    
    class CythonCommand(build_ext):
        """Custom distutils command subclassed from Cython.Distutils.build_ext
        to compile pyx->c, and stop there. All this does is override the 
        C-compile method build_extension() with a no-op."""
        def build_extension(self, ext):
            pass
    
    cmdclass['cython'] = CythonCommand
    cmdclass['build_ext'] =  build_ext
    cmdclass['sdist'] =  CheckSDist

if sys.platform == 'win32':
    libzmq = 'libzmq'
else:
    libzmq = 'zmq'

extensions = []
for submod, packages in submodules.items():
    for pkg in sorted(packages):
        sources = [pjoin('zmq', submod, pkg+suffix)]
        if suffix == '.pyx':
            sources.extend(packages[pkg])
        ext = Extension(
            'zmq.%s.%s'%(submod, pkg),
            sources = sources,
            libraries = [libzmq],
            include_dirs = includes,
            extra_compile_args = extra_flags
        )
        extensions.append(ext)

#
package_data = {'zmq':['*.pxd'],
                'zmq.core':['*.pxd'],
                'zmq.devices':['*.pxd'],
                'zmq.utils':['*.pxd', '*.h'],
}

if release:
    for pkg,data in pkgdata.iteritems():
        data.append('*.c')
        
#-----------------------------------------------------------------------------
# Main setup
#-----------------------------------------------------------------------------

long_desc = \
"""
PyZMQ is a lightweight and super-fast messaging library built on top of
the ZeroMQ library (http://www.zeromq.org). 
"""

setup(
    name = "pyzmq",
    version = "2.0.9dev",
    packages = ['zmq', 'zmq.tests', 'zmq.eventloop', 'zmq.log', 'zmq.core',
                'zmq.devices', 'zmq.utils'],
    ext_modules = extensions,
    package_data = package_data,
    author = "Brian E. Granger",
    author_email = "ellisonbg@gmail.com",
    url = 'http://github.com/zeromq/pyzmq',
    download_url = 'http://github.com/zeromq/pyzmq/downloads',
    description = "Python bindings for 0MQ.",
    long_description = long_desc, 
    license = "LGPL",
    cmdclass = cmdclass,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Topic :: System :: Networking'
    ]
)

