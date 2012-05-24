#!/usr/bin/env python


#-----------------------------------------------------------------------------
#  Copyright (c) 2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#
#  The `configure` subcommand is copied and adaped from h5py
#  h5py source used under the New BSD license
#
#  h5py: <http://code.google.com/p/h5py/>
#-----------------------------------------------------------------------------

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
    lib_ext = '.dylib'
else:
    lib_ext = '.so'

# whether any kind of bdist is happening
doing_bdist = any(arg.startswith('bdist') for arg in sys.argv[1:])

#-----------------------------------------------------------------------------
# Configuration (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------


ZMQ = discover_settings()

if ZMQ is not None and not os.path.exists(ZMQ):
    warn("ZMQ directory \"%s\" does not appear to exist" % ZMQ)

# bundle_libzmq flag for whether libzmq will be included in pyzmq:
if sys.platform.startswith('win'):
    bundle_libzmq = True
elif ZMQ is not None:
    bundle_libzmq = doing_bdist
else:
    bundle_libzmq = False

# --- compiler settings -------------------------------------------------

def settings_from_prefix(zmq=None):
    """load appropriate library/include settings from ZMQ prefix"""
    if sys.platform.startswith('win'):
        settings = {
            'libraries'     : ['libzmq'],
            'include_dirs'  : [],
            'library_dirs'  : [],
        }
        if zmq is not None:
            settings['include_dirs'] += [pjoin(zmq, 'include')]
            settings['library_dirs'] += [pjoin(zmq, 'lib')]
    else:
        settings = {
           'libraries'      : ['zmq'],
           'include_dirs'   : [],
           'library_dirs'   : [],
           'define_macros'  : [('PYZMQ_POSIX', 1)],
        }
    
        # add pthread on freebsd
        if sys.platform.startswith('freebsd'):
            settings['libraries'].append('pthread')
    
        if zmq is not None:
            settings['include_dirs'] += [pjoin(zmq, 'include')]
            settings['library_dirs'] += [pjoin(zmq, 'lib')]
        elif sys.platform == 'darwin' and os.path.isdir('/opt/local/lib'):
            # allow macports default
            settings['include_dirs'] += ['/opt/local/include']
            settings['library_dirs'] += ['/opt/local/lib']
    
        if bundle_libzmq:
            # bdist should link against bundled libzmq
            settings['library_dirs'] = ['zmq']
            if sys.platform == 'darwin':
                pass
                # unused rpath args for OSX:
                # settings['extra_link_args'] = ['-Wl,-rpath','-Wl,$ORIGIN/..']
            else:
                settings['runtime_library_dirs'] = ['$ORIGIN/..']
        elif sys.platform != 'darwin':
            settings['runtime_library_dirs'] = [os.path.abspath(x) for x in settings['library_dirs']]

    # suppress common warnings

    extra_flags = []
    if ignore_common_warnings:
        for warning in ('unused-function', 'strict-aliasing'):
            extra_flags.append('-Wno-'+warning)

    settings['extra_compile_args'] = extra_flags
    
    # include internal directories
    settings['include_dirs'] += [pjoin('zmq', sub) for sub in ('utils','core','devices')]

    return settings

COMPILER_SETTINGS = settings_from_prefix(ZMQ)


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
        self.zmq = ZMQ
        self.settings = copy.copy(COMPILER_SETTINGS)
    
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
        zmq = self.zmq
        if zmq is not None and not os.path.isdir(zmq):
            fatal("Custom zmq directory \"%s\" does not exist" % zmq)

        config = self.getcached()
        if config is None or config['options'] != self.settings:
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
        settings = self.settings
        if bundle_libzmq and not sys.platform.startswith('win'):
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
            print ("    Custom ZMQ dir:       %s" % (self.zmq,))
            config = detect_zmq(self.tempdir, **settings)
        except Exception:
            # if zmq unspecified on *ix, try again with explicit /usr/local
            if self.zmq is None and not sys.platform.startswith('win'):
                self.erase_tempdir()
                print ("Failed with default libzmq, trying again with /usr/local")
                self.zmq = '/usr/local'
                self.settings = settings_from_prefix(self.zmq)
                
                self.run()
                # if we get here the second run succeeded, so we need to update compiler
                # settings for the extensions with /usr/local prefix
                for ext in self.distribution.ext_modules:
                    for key,value in self.settings.iteritems():
                        setattr(ext, key, value)
                return
            
            etype, evalue, tb = sys.exc_info()
            # print the error as distutils would if we let it raise:
            print ("error: %s" % evalue)
            if etype is CompileError:
                action = 'compile'
            elif etype is LinkError:
                action = 'link'
            else:
                action = 'build or run'
            
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
        self.version_py = pjoin('zmq','core','version.py')
    
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
        
        # now that we have the git revision, we can apply it to version.py
        with open(self.version_py) as f:
            lines = f.readlines()
        
        for i,line in enumerate(lines):
            if line.startswith('__revision__'):
                lines[i] = "__revision__ = '%s'\n"%rev
                break
        with open(self.version_py, 'w') as f:
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
        if bundle_libzmq and not sys.platform.startswith('win'):
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
# Extensions
#-----------------------------------------------------------------------------

cmdclass = {'test':TestCommand, 'clean':CleanCommand, 'revision':GitRevisionCommand,
            'configure': Configure, 'build': CopyingBuild}

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
            '_poll':[libzmq, socket, context],
            'stopwatch':[libzmq, pxd('core','stopwatch')],
            'context':[context, libzmq],
            'message':[libzmq, buffers, message],
            'socket':[context, message, socket, libzmq, buffers],
            'device':[libzmq, socket, context],
            '_version':[libzmq],
    },
    devices = {
            'monitoredqueue':[buffers, libzmq, monqueue, socket, context],
    },
    utils = {
            'initthreads':[libzmq],
            'rebuffer':[buffers],
    },
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

if bundle_libzmq:
    package_data['zmq'].append('libzmq'+lib_ext)

def extract_version():
    """extract pyzmq version from core/version.py, so it's not multiply defined"""
    with open(pjoin('zmq', 'core', 'version.py')) as f:
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
    license = "LGPL+BSD",
    cmdclass = cmdclass,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Topic :: System :: Networking',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
    ]
)

