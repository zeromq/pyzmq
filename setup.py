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
#    The `configure` subcommand is copied and adaped from h5py
#    h5py source used under the New BSD license
#
#    h5py: <http://code.google.com/p/h5py/>
#    BSD license: <http://www.opensource.org/licenses/bsd-license.php>
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import with_statement

import copy
import os
import re
import shutil
import sys
from traceback import print_exc

from distutils.core import setup, Command
from distutils.ccompiler import get_default_compiler
from distutils.extension import Extension
from distutils.errors import CompileError, LinkError
from distutils.command.build import build
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist

from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin

from subprocess import Popen, PIPE
import logging

try:
    from configparser import ConfigParser
except:
    from ConfigParser import ConfigParser

try:
    import nose
except ImportError:
    nose = None

# local script imports:
from buildutils import (discover_settings, v_str, localpath, savepickle, loadpickle, detect_zmq,
                        warn, fatal, copy_and_patch_libzmq)

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

# the minimum zeromq version this will work against:
min_zmq = (2,1,4)

# set dylib ext:
if sys.platform.startswith('win'):
    lib_ext = '.dll'
elif sys.platform == 'darwin':
    lib_ext = '.1.dylib'
else:
    lib_ext = '.so.1'

# whether any kind of bdist is happening
doing_bdist = any(arg.startswith('bdist') for arg in sys.argv[1:])

#-----------------------------------------------------------------------------
# Configuration (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------


ZMQ = discover_settings()

if ZMQ is not None and not os.path.exists(ZMQ):
    warn("ZMQ directory \"%s\" does not appear to exist" % ZMQ)

# --- compiler settings -------------------------------------------------

if sys.platform.startswith('win'):
    COMPILER_SETTINGS = {
        'libraries'     : ['libzmq'],
        'include_dirs'  : [],
        'library_dirs'  : [],
    }
    if ZMQ is not None:
        COMPILER_SETTINGS['include_dirs'] += [pjoin(ZMQ, 'include')]
        COMPILER_SETTINGS['library_dirs'] += [pjoin(ZMQ, 'lib')]
else:
    COMPILER_SETTINGS = {
       'libraries'      : ['zmq'],
       'include_dirs'   : [],
       'library_dirs'   : [],
    }
    
    # add pthread on freebsd
    if sys.platform.startswith('freebsd'):
        COMPILER_SETTINGS['libraries'].append('pthread')
    
    if ZMQ is not None:
        COMPILER_SETTINGS['include_dirs'] += [pjoin(ZMQ, 'include')]
        COMPILER_SETTINGS['library_dirs'] += [pjoin(ZMQ, 'lib')]
    elif sys.platform == 'darwin' and os.path.isdir('/opt/local/lib'):
        # allow macports default
        COMPILER_SETTINGS['include_dirs'] += ['/opt/local/include']
        COMPILER_SETTINGS['library_dirs'] += ['/opt/local/lib']
    
    if doing_bdist:
        # bdist should link against bundled libzmq
        COMPILER_SETTINGS['library_dirs'] = ['zmq']
        if sys.platform == 'darwin':
            pass
            # unused rpath args for OSX:
            # COMPILER_SETTINGS['extra_link_args'] = ['-Wl,-rpath','-Wl,$ORIGIN/..']
        else:
            COMPILER_SETTINGS['runtime_library_dirs'] = ['$ORIGIN/..']
    elif sys.platform != 'darwin':
        COMPILER_SETTINGS['runtime_library_dirs'] = [os.path.abspath(x) for x in COMPILER_SETTINGS['library_dirs']]


#-----------------------------------------------------------------------------
# Extra commands
#-----------------------------------------------------------------------------

class Configure(Command):
    """Configure command adapted from h5py"""

    description = "Discover ZMQ version and features"

    # DON'T REMOVE: distutils demands these be here even if they do nothing.
    user_options = []
    boolean_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    tempdir = 'detect'

    def create_tempdir(self):
        self.erase_tempdir()
        os.mkdir(self.tempdir)
        if sys.platform.startswith('win'):
            # fetch libzmq.dll into local dir
            local_dll = pjoin(self.tempdir, 'libzmq.dll')
            if ZMQ is None and not os.path.exists(local_dll):
                fatal("ZMQ directory must be specified on Windows via setup.cfg or 'python setup.py configure --zmq=/path/to/zeromq2'")
            
            try:
                shutil.copy(pjoin(ZMQ, 'lib', 'libzmq.dll'), local_dll)
            except Exception:
                if not os.path.exists(local_dll):
                    warn("Could not copy libzmq into zmq/, which is usually necessary on Windows."
                    "Please specify zmq prefix via configure --zmq=/path/to/zmq or copy "
                    "libzmq into zmq/ manually.")
            

    def erase_tempdir(self):
        try:
            shutil.rmtree(self.tempdir)
        except Exception:
            pass

    def getcached(self):
        return loadpickle('configure.pickle')

    def check_zmq_version(self):
        zmq = ZMQ
        if zmq is not None and not os.path.isdir(zmq):
            fatal("Custom zmq directory \"%s\" does not exist" % zmq)

        config = self.getcached()
        if config is None or config['options'] != COMPILER_SETTINGS:
            self.run()
            config = self.config
        else:
            self.config = config

        vers = config['vers']
        vs = v_str(vers)
        if vers < min_zmq:
            fatal("Detected ZMQ version: %s, but depend on zmq >= %s"%(
                    vs, v_str(min_zmq))
                    +'\n       Using ZMQ=%s'%(zmq or 'unspecified'))
        pyzmq_version = extract_version().strip('abcdefghijklmnopqrstuvwxyz')

        if vs < pyzmq_version:
            warn("Detected ZMQ version: %s, but pyzmq targets zmq %s."%(
                    vs, pyzmq_version))
            warn("libzmq features and fixes introduced after %s will be unavailable."%vs)
            print('*'*42)
        elif vs >= '3.0':
            warn("Detected ZMQ version: %s. pyzmq's support for libzmq-dev is experimental."%vs)
            print('*'*42)

        if sys.platform.startswith('win'):
            # fetch libzmq.dll into local dir
            local_dll = localpath('zmq','libzmq.dll')
            if zmq is None and not os.path.exists(local_dll):
                fatal("ZMQ directory must be specified on Windows via setup.cfg or 'python setup.py configure --zmq=/path/to/zeromq2'")
            try:
                shutil.copy(pjoin(zmq, 'lib', 'libzmq.dll'), local_dll)
            except Exception:
                if not os.path.exists(local_dll):
                    warn("Could not copy libzmq into zmq/, which is usually necessary on Windows."
                    "Please specify zmq prefix via configure --zmq=/path/to/zmq or copy "
                    "libzmq into zmq/ manually.")

    def run(self):
        self.create_tempdir()
        settings = copy.copy(COMPILER_SETTINGS)
        if doing_bdist and not sys.platform.startswith('win'):
            # rpath slightly differently here, because libzmq not in .. but ../zmq:
            settings['library_dirs'] = ['zmq']
            if sys.platform == 'darwin':
                pass
                # unused rpath args for OSX:
                # settings['extra_link_args'] = ['-Wl,-rpath','-Wl,$ORIGIN/../zmq']
            else:
                settings['runtime_library_dirs'] = ['$ORIGIN/../zmq']
        try:
            print ("*"*42)
            print ("Configure: Autodetecting ZMQ settings...")
            print ("    Custom ZMQ dir:       %s" % (ZMQ,))
            config = detect_zmq(self.tempdir, **settings)
        except Exception:
            etype = sys.exc_info()[0]
            if etype is CompileError:
                action = 'compile'
            elif etype is LinkError:
                action = 'link'
            else:
                action = 'run'
            fatal("""
    Failed to %s ZMQ test program.  Please check to make sure:

    * You have a C compiler installed
    * A development version of Python is installed (including header files)
    * A development version of ZMQ >= %s is installed (including header files)
    * If ZMQ is not in a default location, supply the argument --zmq=<path>
    * If you did recently install ZMQ to a default location, 
      try rebuilding the ld cache with `sudo ldconfig`
      or specify zmq's location with `--zmq=/usr/local`
    """%(action, v_str(min_zmq)))
            
        else:
            savepickle('configure.pickle', config)
            print ("    ZMQ version detected: %s" % v_str(config['vers']))
        finally:
            print ("*"*42)
            self.erase_tempdir()
        self.config = config

class TestCommand(Command):
    """Custom distutils command to run the test suite."""

    user_options = [ ]

    def initialize_options(self):
        self._dir = os.getcwd()

    def finalize_options(self):
        pass
    
    def run_nose(self):
        """Run the test suite with nose."""
        return nose.core.TestProgram(argv=["", '-vv', pjoin(self._dir, 'zmq', 'tests')])
    
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
            fatal('\n       '.join(["Could not import zmq!",
            "You must build pyzmq with 'python setup.py build_ext --inplace' for 'python setup.py test' to work.",
            "If you did build pyzmq in-place, then this is a real error."]))
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
        
        line = p.stdout.readline().decode().strip()
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
        self._clean_trees = []
        for root, dirs, files in list(os.walk('zmq')):
            for f in files:
                if os.path.splitext(f)[-1] in ('.pyc', '.so', '.o', '.pyd'):
                    self._clean_me.append(pjoin(root, f))
            for d in dirs:
                if d == '__pycache__':
                    self._clean_trees.append(pjoin(root, d))
        
        for d in ('build',):
            if os.path.exists(d):
                self._clean_trees.append(d)

        bundled = glob(pjoin('zmq', 'libzmq*'))
        self._clean_me.extend(bundled)
        


    def finalize_options(self):
        pass

    def run(self):
        for clean_me in self._clean_me:
            try:
                os.unlink(clean_me)
            except Exception:
                pass
        for clean_tree in self._clean_trees:
            try:
                shutil.rmtree(clean_tree)
            except Exception:
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
        if 'cython' in cmdclass:
            self.run_command('cython')
        else:
            for pyxfile in self._pyxfiles:
                cfile = pyxfile[:-3]+'c'
                msg = "C-source file '%s' not found."%(cfile)+\
                " Run 'setup.py cython' before sdist."
                assert os.path.isfile(cfile), msg
        sdist.run(self)

class CopyingBuild(build):
    """subclass of build that copies libzmq if doing bdist."""
    
    def run(self):
        if doing_bdist and not sys.platform.startswith('win'):
            # always rebuild before bdist, because linking may be wrong:
            self.run_command('clean')
            copy_and_patch_libzmq(ZMQ, 'libzmq'+lib_ext)
        build.run(self)

class CheckingBuildExt(build_ext):
    """Subclass build_ext to get clearer report if Cython is neccessary."""
    
    def check_cython_extensions(self, extensions):
        for ext in extensions:
          for src in ext.sources:
            if not os.path.exists(src):
                fatal("""Cython-generated file '%s' not found.
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
        configure = self.distribution.get_command_obj('configure')
        configure.check_zmq_version()
        build_ext.run(self)
    

#-----------------------------------------------------------------------------
# Suppress Common warnings
#-----------------------------------------------------------------------------

extra_flags = []
if ignore_common_warnings:
    for warning in ('unused-function', 'strict-aliasing'):
        extra_flags.append('-Wno-'+warning)

COMPILER_SETTINGS['extra_compile_args'] = extra_flags

#-----------------------------------------------------------------------------
# Extensions
#-----------------------------------------------------------------------------

cmdclass = {'test':TestCommand, 'clean':CleanCommand, 'revision':GitRevisionCommand,
            'configure': Configure, 'build': CopyingBuild}

COMPILER_SETTINGS['include_dirs'] += [pjoin('zmq', sub) for sub in ('utils','core','devices')]

def pxd(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.pxd'))

def pyx(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.pyx'))

def dotc(subdir, name):
    return os.path.abspath(pjoin('zmq', subdir, name+'.c'))

libzmq = pxd('core', 'libzmq')
buffers = pxd('utils', 'buffers')
message = pxd('core', 'message')
context = pxd('core', 'context')
socket = pxd('core', 'socket')
monqueue = pxd('devices', 'monitoredqueue')

submodules = dict(
    core = {'constants': [libzmq],
            'error':[libzmq],
            'poll':[libzmq, socket],
            'stopwatch':[libzmq, pxd('core','stopwatch')],
            'context':[context, libzmq],
            'message':[libzmq, buffers, message],
            'socket':[context, message, socket, libzmq, buffers],
            'device':[libzmq, socket, context],
            'version':[libzmq],
    },
    devices = {
            'monitoredqueue':[buffers, libzmq, monqueue, socket, context],
    },
    utils = {
            'initthreads':[libzmq],
            'rebuffer':[buffers],
    }
)

try:
    from Cython.Distutils import build_ext
    cython=True
except ImportError:
    cython=False
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
    
    class zbuild_ext(build_ext):
        def run(self):
            configure = self.distribution.get_command_obj('configure')
            configure.check_zmq_version()
            return build_ext.run(self)
    
    cmdclass['cython'] = CythonCommand
    cmdclass['build_ext'] =  zbuild_ext
    cmdclass['sdist'] =  CheckSDist

extensions = []
for submod, packages in submodules.items():
    for pkg in sorted(packages):
        sources = [pjoin('zmq', submod, pkg+suffix)]
        if suffix == '.pyx':
            sources.extend(packages[pkg])
        ext = Extension(
            'zmq.%s.%s'%(submod, pkg),
            sources = sources,
            **COMPILER_SETTINGS
        )
        extensions.append(ext)

#
package_data = {'zmq':['*.pxd'],
                'zmq.core':['*.pxd'],
                'zmq.devices':['*.pxd'],
                'zmq.utils':['*.pxd', '*.h'],
}

if sys.platform.startswith('win') or doing_bdist:
    package_data['zmq'].append('libzmq'+lib_ext)

def extract_version():
    """extract pyzmq version from core/version.pyx, so it's not multiply defined"""
    with open(pjoin('zmq', 'core', 'version.pyx')) as f:
        line = f.readline()
        while not line.startswith("__version__"):
            line = f.readline()
    exec(line, globals())
    if 'bdist_msi' in sys.argv:
        # msi has strict version requirements, which requires that
        # we strip any dev suffix
        return re.match(r'\d+(\.\d+)+', __version__).group()
    else:
        return __version__

def find_packages():
    """adapted from IPython's setupbase.find_packages()"""
    packages = []
    for dir,subdirs,files in os.walk('zmq'):
        package = dir.replace(os.path.sep, '.')
        if '__init__.py' not in files:
            # not a package
            continue
        packages.append(package)
    return packages

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
    packages = find_packages(),
    ext_modules = extensions,
    package_data = package_data,
    author = "Brian E. Granger, Min Ragan-Kelley",
    author_email = "zeromq-dev@lists.zeromq.org",
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
        'Topic :: System :: Networking',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
    ]
)

