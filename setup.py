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
from __future__ import with_statement

import os, sys
from traceback import print_exc

from distutils.core import setup, Command
from distutils.ccompiler import get_default_compiler
from distutils.extension import Extension
from distutils.command.sdist import sdist
from distutils.command.build_ext import build_ext

from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin

from subprocess import Popen, PIPE

from zmqversion import check_zmq_version

try:
    import nose
except ImportError:
    nose = None

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
    ignore_common_warnings=False

release = False # flag for whether to include *.c in package_data

# the minimum zeromq version this will work against:
min_zmq = (2,1,0)

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
    
    def run_nose(self):
        """Run the test suite with nose."""
        return nose.core.TestProgram(argv=["", '-vvs', pjoin(self._dir, 'zmq', 'tests')])
    
    def run_unittest(self):
        """Finds all the tests modules in zmq/tests/ and runs them."""
        testfiles = [ ]
        for t in glob(pjoin(self._dir, 'zmq', 'tests', '*.py')):
            name = splitext(basename(t))[0]
            if name.startswith('test_'):
                testfiles.append('.'.join(
                    ['zmq.tests', name])
                )
        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = 2)
        t.run(tests)
    
    def run(self):
        """Run the test suite, with nose, or unittest if nose is unavailable"""
        # crude check for inplace build:
        try:
            import zmq
        except ImportError:
            print_exc()
            print ("Could not import zmq!")
            print ("You must build pyzmq with 'python setup.py build_ext --inplace' for 'python setup.py test' to work.")
            print ("If you did build pyzmq in-place, then this is a real error.")
            sys.exit(1)
        
        if nose is None:
            print ("nose unavailable, falling back on unittest. Skipped tests will appear as ERRORs.")
            return self.run_unittest()
        else:
            return self.run_nose()

class GitRevisionCommand(Command):
    """find the current git revision and add it to zmq.core.verion.__revision__"""
    
    user_options = [ ]
    
    def initialize_options(self):
        self.version_pyx = pjoin('zmq','core','version.pyx')
    
    def run(self):
        try:
            p = Popen('git log -1'.split(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        except IOError:
            print ("No git found, skipping git revision")
            return
        
        if p.wait():
            print ("checking git branch failed")
            print (p.stderr.read())
            return
        
        line = p.stdout.readline().strip()
        if not line.startswith('commit'):
            print ("bad commit line: %r"%line)
            return
        
        rev = line.split()[-1]
        
        # now that we have the git revision, we can apply it to version.pyx
        with open(self.version_pyx) as f:
            lines = f.readlines()
        
        for i,line in enumerate(lines):
            if line.startswith('__revision__'):
                lines[i] = "__revision__ = '%s'\n"%rev
                break
        with open(self.version_pyx, 'w') as f:
            f.writelines(lines)
    
    def finalize_options(self):
        pass

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
        for root, dirs, files in os.walk('zmq'):
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
    
    def run(self):
        # check version, to prevent confusing undefined constant errors
        check_zmq_version(min_zmq)
        build_ext.run(self)
    

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

cmdclass = {'test':TestCommand, 'clean':CleanCommand, 'revision':GitRevisionCommand}

includes = [pjoin('zmq', sub) for sub in ('utils','core','devices')]

def pxd(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.pxd'))

def pyx(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.pyx'))

def dotc(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.c'))

czmq = pxd('core', 'czmq')
buffers = pxd('utils', 'buffers')
message = pxd('core', 'message')
context = pxd('core', 'context')
socket = pxd('core', 'socket')

submodules = dict(
    core = {'constants': [czmq],
            'error':[czmq],
            'poll':[czmq],
            'stopwatch':[czmq, pxd('core','stopwatch')],
            'context':[socket, context, czmq],
            'message':[czmq, buffers, message],
            'socket':[context, message, socket, czmq, buffers],
            'device':[czmq],
            'version':[czmq],
    },
    devices = {
            'monitoredqueue':[buffers, czmq],
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
    
    class CheckZMQBuildExt(build_ext):
        def run(self):
            check_zmq_version(min_zmq)
            return build_ext.run(self)
    
    cmdclass['cython'] = CythonCommand
    cmdclass['build_ext'] =  CheckZMQBuildExt
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
    for pkg,data in package_data.iteritems():
        data.append('*.c')

def extract_version():
    """extract pyzmq version from core/version.pyx, so it's not multiply defined"""
    with open(pjoin('zmq', 'core', 'version.pyx')) as f:
        line = f.readline()
        while not line.startswith("__version__"):
            line = f.readline()
    exec(line, globals())
    return __version__

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
    version = extract_version(),
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

