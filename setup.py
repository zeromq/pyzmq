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
#
#  The code to bundle libzmq as an Extension is from pyzmq-static
#  pyzmq-static source used under the New BSD license
#
#  pyzmq-static: <https://github.com/brandon-rhodes/pyzmq-static>
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
import time
import errno
from traceback import print_exc

if sys.version_info < (2,6):
    print("ERROR: PyZMQ >= 2.2.0 requires Python 2.6 or later.  \n" +
          "       PyZMQ 2.1.11 was the last release to support Python 2.5."
    )
    sys.exit(1)


import distutils
from distutils.core import setup, Command
from distutils.ccompiler import get_default_compiler
from distutils.ccompiler import new_compiler
from distutils.extension import Extension
from distutils.errors import CompileError, LinkError
from distutils.command.build import build
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist
from distutils.version import LooseVersion as V

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
from buildutils import (
    discover_settings, v_str, save_config, load_config, detect_zmq, merge,
    config_from_prefix,
    info, warn, fatal, debug, line, copy_and_patch_libzmq, localpath,
    fetch_libzmq, stage_platform_hpp,
    bundled_version, customize_mingw,
    test_compilation, compile_and_run,
    )

#-----------------------------------------------------------------------------
# Flags
#-----------------------------------------------------------------------------

# reference points for zmq compatibility
min_zmq = (2,1,4)
target_zmq = bundled_version
dev_zmq = (4,1,0)

# set dylib ext:
if sys.platform.startswith('win'):
    lib_ext = '.dll'
elif sys.platform == 'darwin':
    lib_ext = '.dylib'
else:
    lib_ext = '.so'

# whether any kind of bdist is happening
doing_bdist = any(arg.startswith('bdist') for arg in sys.argv[1:])

# allow `--zmq=foo` to be passed at any point,
# but always assign it to configure

configure_idx = -1
fetch_idx = -1
for idx, arg in enumerate(list(sys.argv)):
    # track index of configure and fetch_libzmq
    if arg == 'configure':
        configure_idx = idx
    elif arg == 'fetch_libzmq':
        fetch_idx = idx
    
    if arg.startswith('--zmq='):
        sys.argv.pop(idx)
        if configure_idx < 0:
            if fetch_idx < 0:
                configure_idx = 1
            else:
                configure_idx = fetch_idx + 1
            sys.argv.insert(configure_idx, 'configure')
        sys.argv.insert(configure_idx + 1, arg)
        break

#-----------------------------------------------------------------------------
# Configuration (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------

# --- compiler settings -------------------------------------------------

def bundled_settings():
    """settings for linking extensions against bundled libzmq"""
    settings = {}
    settings['libraries'] = []
    settings['library_dirs'] = []
    settings['include_dirs'] = [pjoin("bundled", "zeromq", "include")]
    settings['runtime_library_dirs'] = []
    # add pthread on freebsd
    # is this necessary?
    if sys.platform.startswith('freebsd'):
        settings['libraries'].append('pthread')
    elif sys.platform.startswith('win'):
        # link against libzmq in build dir:
        plat = distutils.util.get_platform()
        temp = 'temp.%s-%s' % (plat, sys.version[0:3])
        settings['libraries'].append('libzmq')
        settings['library_dirs'].append(pjoin('build', temp, 'Release', 'buildutils'))
    
    return settings


def settings_from_prefix(prefix=None, bundle_libzmq_dylib=False):
    """load appropriate library/include settings from ZMQ prefix"""
    settings = {}
    settings['libraries'] = []
    settings['include_dirs'] = []
    settings['library_dirs'] = []
    settings['runtime_library_dirs'] = []
    
    if sys.platform.startswith('win'):
        settings['libraries'].append('libzmq')
        
        if prefix:
            settings['include_dirs'] += [pjoin(prefix, 'include')]
            settings['library_dirs'] += [pjoin(prefix, 'lib')]
    else:

        # If prefix is not explicitly set, pull it from pkg-config by default.

        if not prefix:
            try:
                p = Popen('pkg-config --variable=prefix --print-errors libzmq'.split(), stdout=PIPE, stderr=PIPE)
            except OSError as e:
                if e.errno == errno.ENOENT:
                    info("pkg-config not found")
                else:
                    warn("Running pkg-config failed - %s." % e)
                p = None
            if p is not None:
                if p.wait():
                    info("Did not find libzmq via pkg-config:")
                    info(p.stderr.read().decode())
                else:
                    prefix = p.stdout.readline().strip().decode()
                    info("Using zmq-prefix %s (found via pkg-config)." % prefix)

        settings['libraries'].append('zmq')
        # add pthread on freebsd
        if sys.platform.startswith('freebsd'):
            settings['libraries'].append('pthread')
    
        if prefix:
            settings['include_dirs'] += [pjoin(prefix, 'include')]
            if not bundle_libzmq_dylib:
                settings['library_dirs'] += [pjoin(prefix, 'lib')]
        else:
            if sys.platform == 'darwin' and os.path.isdir('/opt/local/lib'):
                # allow macports default
                settings['include_dirs'] += ['/opt/local/include']
                settings['library_dirs'] += ['/opt/local/lib']
            if os.environ.get('VIRTUAL_ENV', None):
                # find libzmq installed in virtualenv
                env = os.environ['VIRTUAL_ENV']
                settings['include_dirs'] += [pjoin(env, 'include')]
                settings['library_dirs'] += [pjoin(env, 'lib')]
    
        if bundle_libzmq_dylib:
            # bdist should link against bundled libzmq
            settings['library_dirs'].append('zmq')
            if sys.platform == 'darwin':
                pass
                # unused rpath args for OS X:
                # settings['extra_link_args'] = ['-Wl,-rpath','-Wl,$ORIGIN/..']
            else:
                settings['runtime_library_dirs'] += ['$ORIGIN/..']
        elif sys.platform != 'darwin':
            settings['runtime_library_dirs'] += [
                os.path.abspath(x) for x in settings['library_dirs']
            ]
    
    return settings


#-----------------------------------------------------------------------------
# Extra commands
#-----------------------------------------------------------------------------

class Configure(build_ext):
    """Configure command adapted from h5py"""

    description = "Discover ZMQ version and features"
    
    user_options = build_ext.user_options + [
        ('zmq=', None, "libzmq install prefix"),
        ('build-base=', 'b', "base directory for build library"), # build_base from build
        
    ]
    def initialize_options(self):
        build_ext.initialize_options(self)
        self.zmq = None
        self.build_base = 'build'

    # DON'T REMOVE: distutils demands these be here even if they do nothing.
    def finalize_options(self):
        build_ext.finalize_options(self)
        self.tempdir = pjoin(self.build_temp, 'scratch')
        self.has_run = False
        self.config = discover_settings(self.build_base)
        if self.zmq is not None:
            merge(self.config, config_from_prefix(self.zmq))
        self.init_settings_from_config()
    
    def save_config(self, name, cfg):
        """write config to JSON"""
        save_config(name, cfg, self.build_base)
    
    def init_settings_from_config(self):
        """set up compiler settings, based on config"""
        if 'PyPy' in sys.version:
            self.compiler_settings = {}
        cfg = self.config
        
        if cfg['libzmq_extension']:
            settings = bundled_settings()
        else:
            settings = settings_from_prefix(cfg['zmq_prefix'], self.bundle_libzmq_dylib)
    
        if 'have_sys_un_h' not in cfg:
            # don't link against anything when checking for sys/un.h
            minus_zmq = copy.deepcopy(settings)
            try:
                minus_zmq['libraries'] = []
            except Exception:
                pass
            try:
                compile_and_run(self.tempdir,
                    pjoin('buildutils', 'check_sys_un.c'),
                    **minus_zmq
                )
            except Exception as e:
                warn("No sys/un.h, IPC_PATH_MAX_LEN will be undefined: %s" % e)
                cfg['have_sys_un_h'] = False
            else:
                cfg['have_sys_un_h'] = True
        
            self.save_config('config', cfg)
    
        if cfg['have_sys_un_h']:
            settings['define_macros'] = [('HAVE_SYS_UN_H', 1)]
    
        settings.setdefault('define_macros', [])
    
        # include internal directories
        settings.setdefault('include_dirs', [])
        settings['include_dirs'] += [pjoin('zmq', sub) for sub in (
            'utils',
            pjoin('backend', 'cython'),
            'devices',
        )]
        
        for ext in self.distribution.ext_modules:
            if ext.name == 'zmq.libzmq':
                continue
            for attr, value in settings.items():
                setattr(ext, attr, value)
        
        self.compiler_settings = settings
        self.save_config('compiler', settings)

    def create_tempdir(self):
        self.erase_tempdir()
        os.makedirs(self.tempdir)
        if sys.platform.startswith('win'):
            # fetch libzmq.dll into local dir
            local_dll = pjoin(self.tempdir, 'libzmq.dll')
            if not self.config['zmq_prefix'] and not os.path.exists(local_dll):
                fatal("ZMQ directory must be specified on Windows via setup.cfg"
                " or 'python setup.py configure --zmq=/path/to/zeromq2'")
            
            try:
                shutil.copy(pjoin(self.config['zmq_prefix'], 'lib', 'libzmq.dll'), local_dll)
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

    @property
    def compiler_type(self):
        compiler = self.compiler
        if compiler is None:
            return get_default_compiler()
        elif isinstance(compiler, str):
            return compiler
        else:
            return compiler.compiler_type
    
    @property
    def cross_compiling(self):
        return self.config['bdist_egg'].get('plat-name', sys.platform) != sys.platform

    @property
    def bundle_libzmq_dylib(self):
        """
        bundle_libzmq_dylib flag for whether external libzmq library will be included in pyzmq:
        only relevant when not building libzmq extension
        """
        if 'bundle_libzmq_dylib' in self.config:
            return self.config['bundle_libzmq_dylib']
        elif (sys.platform.startswith('win') or self.cross_compiling) \
                and not self.config['libzmq_extension']:
            # always bundle libzmq on Windows and cross-compilation
            return True
        elif self.config['zmq_prefix'] and not self.config['libzmq_extension']:
            # only bundle for bdists in sane environments
            return doing_bdist
        else:
            return False

    def check_zmq_version(self):
        """check the zmq version"""
        cfg = self.config
        
        # build test program
        zmq_prefix = self.config['zmq_prefix']
        detected = self.test_build(zmq_prefix, self.compiler_settings)
        # now check the libzmq version
        
        vers = tuple(detected['vers'])
        vs = v_str(vers)
        if vers < min_zmq:
            fatal("Detected ZMQ version: %s, but depend on zmq >= %s"%(
                    vs, v_str(min_zmq))
                    +'\n       Using ZMQ=%s' % (zmq_prefix or 'unspecified'))
        
        if vers < target_zmq:
            warn("Detected ZMQ version: %s, but pyzmq targets ZMQ %s." % (
                    vs, v_str(target_zmq))
            )
            warn("libzmq features and fixes introduced after %s will be unavailable." % vs)
            line()
        elif vers >= dev_zmq:
            warn("Detected ZMQ version: %s. pyzmq's support for libzmq-dev is experimental." % vs)
            line()

        if sys.platform.startswith('win'):
            # fetch libzmq.dll into local dir
            local_dll = localpath('zmq','libzmq.dll')
            if not zmq_prefix and not os.path.exists(local_dll):
                fatal("ZMQ directory must be specified on Windows via setup.cfg or 'python setup.py configure --zmq=/path/to/zeromq2'")
            try:
                shutil.copy(pjoin(zmq_prefix, 'lib', 'libzmq.dll'), local_dll)
            except Exception:
                if not os.path.exists(local_dll):
                    warn("Could not copy libzmq into zmq/, which is usually necessary on Windows."
                    "Please specify zmq prefix via configure --zmq=/path/to/zmq or copy "
                    "libzmq into zmq/ manually.")

    
    def bundle_libzmq_extension(self):
        bundledir = "bundled"
        if "PyPy" in sys.version:
            fatal("Can't bundle libzmq as an Extension in PyPy (yet!)")
        ext_modules = self.distribution.ext_modules
        if ext_modules and ext_modules[0].name == 'zmq.libzmq':
            # I've already been run
            return
        
        line()
        info("Using bundled libzmq")
        
        # fetch sources for libzmq extension:
        if not os.path.exists(bundledir):
            os.makedirs(bundledir)
        
        fetch_libzmq(bundledir)
        
        stage_platform_hpp(pjoin(bundledir, 'zeromq'))
        
        # construct the Extension:
        
        ext = Extension(
            'zmq.libzmq',
            sources = [pjoin('buildutils', 'initlibzmq.c')] + 
                        glob(pjoin(bundledir, 'zeromq', 'src', '*.cpp')),
            include_dirs = [
                pjoin(bundledir, 'zeromq', 'include'),
            ],
        )
        
        if sys.platform.startswith('win'):
            # include defines from zeromq msvc project:
            ext.define_macros.append(('FD_SETSIZE', 1024))
            ext.define_macros.append(('DLL_EXPORT', 1))
            
            # When compiling the C++ code inside of libzmq itself, we want to
            # avoid "warning C4530: C++ exception handler used, but unwind
            # semantics are not enabled. Specify /EHsc".
            if self.compiler_type == 'msvc':
                ext.extra_compile_args.append('/EHsc')
            elif self.compiler_type == 'mingw32':
                ext.define_macros.append(('ZMQ_HAVE_MINGW32', 1))

            # And things like sockets come from libraries that must be named.

            ext.libraries.extend(['rpcrt4', 'ws2_32', 'advapi32'])
        else:
            ext.include_dirs.append(bundledir)
            
            # check if we need to link against Realtime Extensions library
            cc = new_compiler(compiler=self.compiler_type)
            cc.output_dir = self.build_temp
            if not sys.platform.startswith(('darwin', 'freebsd')) \
                and not cc.has_function('timer_create'):
                    ext.libraries.append('rt')
            
            # check if we *can* link libsodium
            if cc.has_function('crypto_box_keypair', libraries=ext.libraries + ['sodium']):
                ext.libraries.append('sodium')
                ext.define_macros.append(("HAVE_LIBSODIUM", 1))
            else:
                warn("libsodium not found, zmq.CURVE security will be unavailable")
        
        # insert the extension:
        self.distribution.ext_modules.insert(0, ext)
        
        # update other extensions, with bundled settings
        self.config['libzmq_extension'] = True
        self.init_settings_from_config()
        self.save_config('config', self.config)
        
    
    def fallback_on_bundled(self):
        """Couldn't build, fallback after waiting a while"""
        
        line()
        
        warn('\n'.join([
        "Failed to build or run libzmq detection test.",
        "",
        "If you expected pyzmq to link against an installed libzmq, please check to make sure:",
        "",
        "    * You have a C compiler installed",
        "    * A development version of Python is installed (including headers)",
        "    * A development version of ZMQ >= %s is installed (including headers)" % v_str(min_zmq),
        "    * If ZMQ is not in a default location, supply the argument --zmq=<path>",
        "    * If you did recently install ZMQ to a default location,",
        "      try rebuilding the ld cache with `sudo ldconfig`",
        "      or specify zmq's location with `--zmq=/usr/local`",
        "",
        ]))
        
        # ultra-lazy pip detection:
        if 'pip' in ' '.join(sys.argv):
            info('\n'.join([
        "If you expected to get a binary install (egg), we have those for",
        "current Pythons on OS X and Windows. These can be installed with",
        "easy_install, but PIP DOES NOT SUPPORT EGGS.",
        "",
        ]))
        
        info('\n'.join([
            "You can skip all this detection/waiting nonsense if you know",
            "you want pyzmq to bundle libzmq as an extension by passing:",
            "",
            "    `--zmq=bundled`",
            "",
            "I will now try to build libzmq as a Python extension",
            "unless you interrupt me (^C) in the next 10 seconds...",
            "",
        ]))
        
        for i in range(10,0,-1):
            sys.stdout.write('\r%2i...' % i)
            sys.stdout.flush()
            time.sleep(1)
        
        info("")
        
        return self.bundle_libzmq_extension()
        
    
    def test_build(self, prefix, settings):
        """do a test build ob libzmq"""
        self.create_tempdir()
        settings = settings.copy()
        if self.bundle_libzmq_dylib and not sys.platform.startswith('win'):
            # rpath slightly differently here, because libzmq not in .. but ../zmq:
            settings['library_dirs'] = ['zmq']
            if sys.platform == 'darwin':
                pass
                # unused rpath args for OS X:
                # settings['extra_link_args'] = ['-Wl,-rpath','-Wl,$ORIGIN/../zmq']
            else:
                settings['runtime_library_dirs'] = [ os.path.abspath(pjoin('.', 'zmq')) ]
        
        line()
        info("Configure: Autodetecting ZMQ settings...")
        info("    Custom ZMQ dir:       %s" % prefix)
        try:
            detected = detect_zmq(self.tempdir, compiler=self.compiler_type, **settings)
        finally:
            self.erase_tempdir()
        
        info("    ZMQ version detected: %s" % v_str(detected['vers']))
        
        return detected
    
    
    def finish_run(self):
        self.save_config('config', self.config)
        line()
    
    def run(self):
        cfg = self.config
        if 'PyPy' in sys.version:
            info("PyPy: Nothing to configure")
            return
        
        if cfg['libzmq_extension']:
            self.bundle_libzmq_extension()
            self.finish_run()
            return
        
        # When cross-compiling and zmq is given explicitly, we can't testbuild
        # (as we can't testrun the binary), we assume things are alright.
        if cfg['skip_check_zmq'] or self.cross_compiling:
            warn("Skipping zmq version check")
            self.finish_run()
            return
        
        zmq_prefix = cfg['zmq_prefix']
        # There is no available default on Windows, so start with fallback unless
        # zmq was given explicitly, or libzmq extension was explicitly prohibited.
        if sys.platform.startswith("win") and \
                not cfg['no_libzmq_extension'] and \
                not zmq_prefix:
            self.fallback_on_bundled()
            self.finish_run()
            return
        
        if zmq_prefix and self.bundle_libzmq_dylib and not sys.platform.startswith('win'):
            copy_and_patch_libzmq(zmq_prefix, 'libzmq'+lib_ext)
        
        # first try with given config or defaults
        try:
            self.check_zmq_version()
        except Exception:
            etype, evalue, tb = sys.exc_info()
            # print the error as distutils would if we let it raise:
            info("\nerror: %s\n" % evalue)
        else:
            self.finish_run()
            return
        
        # try fallback on /usr/local on *ix if no prefix is given
        if not zmq_prefix and not sys.platform.startswith('win'):
            info("Failed with default libzmq, trying again with /usr/local")
            time.sleep(1)
            zmq_prefix = cfg['zmq_prefix'] = '/usr/local'
            self.init_settings_from_config()
            try:
                self.check_zmq_version()
            except Exception:
                etype, evalue, tb = sys.exc_info()
                # print the error as distutils would if we let it raise:
                info("\nerror: %s\n" % evalue)
            else:
                # if we get here the second run succeeded, so we need to update compiler
                # settings for the extensions with /usr/local prefix
                self.finish_run()
                return
        
        # finally, fallback on bundled
        
        if cfg['no_libzmq_extension']:
            fatal("Falling back on bundled libzmq,"
            " but setup.cfg has explicitly prohibited building the libzmq extension."
            )
        
        self.fallback_on_bundled()
        
        self.finish_run()


class FetchCommand(Command):
    """Fetch libzmq sources, that's it."""
    
    description = "Fetch libzmq sources into bundled/zeromq"
    
    user_options = [ ]
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        # fetch sources for libzmq extension:
        bundledir = "bundled"
        if os.path.exists(bundledir):
            info("Scrubbing directory: %s" % bundledir)
            shutil.rmtree(bundledir)
        if not os.path.exists(bundledir):
            os.makedirs(bundledir)
        fetch_libzmq(bundledir)
        for tarball in glob(pjoin(bundledir, '*.tar.gz')):
            os.remove(tarball)
        


class TestCommand(Command):
    """Custom distutils command to run the test suite."""

    description = "Test PyZMQ (must have been built inplace: `setup.py build_ext --inplace`)"

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
        
        info("Testing pyzmq-%s with libzmq-%s" % (zmq.pyzmq_version(), zmq.zmq_version()))
        
        if nose is None:
            warn("nose unavailable, falling back on unittest. Skipped tests will appear as ERRORs.")
            return self.run_unittest()
        else:
            return self.run_nose()

class GitRevisionCommand(Command):
    """find the current git revision and add it to zmq.sugar.version.__revision__"""
    
    description = "Store current git revision in version.py"
    
    user_options = [ ]
    
    def initialize_options(self):
        self.version_py = pjoin('zmq','sugar','version.py')
    
    def run(self):
        try:
            p = Popen('git log -1'.split(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        except IOError:
            warn("No git found, skipping git revision")
            return
        
        if p.wait():
            warn("checking git branch failed")
            info(p.stderr.read())
            return
        
        line = p.stdout.readline().decode().strip()
        if not line.startswith('commit'):
            warn("bad commit line: %r" % line)
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
    user_options = [('all', 'a',
         "remove all build output, not just temporary by-products")
    ]

    boolean_options = ['all']

    def initialize_options(self):
        self.all = None

    def finalize_options(self):
        pass

    def run(self):
        self._clean_me = []
        self._clean_trees = []
        for root, dirs, files in list(os.walk('buildutils')):
            for f in files:
                if os.path.splitext(f)[-1] == '.pyc':
                    self._clean_me.append(pjoin(root, f))

        for root, dirs, files in list(os.walk('zmq')):
            for f in files:
                if os.path.splitext(f)[-1] in ('.pyc', '.so', '.o', '.pyd'):
                    self._clean_me.append(pjoin(root, f))
                # remove generated cython files
                if self.all and os.path.splitext(f)[-1] == '.c':
                    self._clean_me.append(pjoin(root, f))

            for d in dirs:
                if d == '__pycache__':
                    self._clean_trees.append(pjoin(root, d))
        
        for d in ('build', 'conf'):
            if os.path.exists(d):
                self._clean_trees.append(d)

        bundled = glob(pjoin('zmq', 'libzmq*'))
        self._clean_me.extend(bundled)
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
        self.run_command('fetch_libzmq')
        if 'cython' in cmdclass:
            self.run_command('cython')
        else:
            for pyxfile in self._pyxfiles:
                cfile = pyxfile[:-3]+'c'
                msg = "C-source file '%s' not found."%(cfile)+\
                " Run 'setup.py cython' before sdist."
                assert os.path.isfile(cfile), msg
        sdist.run(self)

class CheckingBuildExt(build_ext):
    """Subclass build_ext to get clearer report if Cython is necessary."""
    
    def check_cython_extensions(self, extensions):
        for ext in extensions:
          for src in ext.sources:
            if not os.path.exists(src):
                fatal("""Cython-generated file '%s' not found.
                Cython >= 0.16 is required to compile pyzmq from a development branch.
                Please install Cython or download a release package of pyzmq.
                """%src)
    
    def build_extensions(self):
        self.check_cython_extensions(self.extensions)
        self.check_extensions_list(self.extensions)
        
        if self.compiler.compiler_type == 'mingw32':
            customize_mingw(self.compiler)
        
        for ext in self.extensions:
            
            self.build_extension(ext)
    
    def run(self):
        # check version, to prevent confusing undefined constant errors
        self.distribution.run_command('configure')
        build_ext.run(self)


class ConstantsCommand(Command):
    """Rebuild templated files for constants
    
    To be run after adding new constants to `utils/constant_names`.
    """
    user_options = []
    def initialize_options(self):
        return 
    
    def finalize_options(self):
        pass
    
    def run(self):
        from buildutils.constants import render_constants
        render_constants()

#-----------------------------------------------------------------------------
# Extensions
#-----------------------------------------------------------------------------

cmdclass = {'test':TestCommand, 'clean':CleanCommand, 'revision':GitRevisionCommand,
            'configure': Configure, 'fetch_libzmq': FetchCommand,
            'sdist': CheckSDist, 'constants': ConstantsCommand,
        }

def makename(path, ext):
    return os.path.abspath(pjoin('zmq', *path)) + ext

pxd = lambda *path: makename(path, '.pxd')
pxi = lambda *path: makename(path, '.pxi')
pyx = lambda *path: makename(path, '.pyx')
dotc = lambda *path: makename(path, '.c')

libzmq = pxd('backend', 'cython', 'libzmq')
buffers = pxd('utils', 'buffers')
message = pxd('backend', 'cython', 'message')
context = pxd('backend', 'cython', 'context')
socket = pxd('backend', 'cython', 'socket')
utils = pxd('backend', 'cython', 'utils')
checkrc = pxd('backend', 'cython', 'checkrc')
monqueue = pxd('devices', 'monitoredqueue')

submodules = {
    'backend.cython' : {'constants': [libzmq, pxi('backend', 'cython', 'constants')],
            'error':[libzmq, checkrc],
            '_poll':[libzmq, socket, context, checkrc],
            'utils':[libzmq, utils, checkrc],
            'context':[context, libzmq, checkrc],
            'message':[libzmq, buffers, message, checkrc],
            'socket':[context, message, socket, libzmq, buffers, checkrc],
            '_device':[libzmq, socket, context, checkrc],
            '_version':[libzmq],
    },
    'devices' : {
            'monitoredqueue':[buffers, libzmq, monqueue, socket, context, checkrc],
    },
    'utils' : {
            'initthreads':[libzmq],
            'rebuffer':[buffers],
    },
}

try:
    import Cython
    if V(Cython.__version__) < V('0.16'):
        raise ImportError("Cython >= 0.16 required, found %s" % Cython.__version__)
    from Cython.Distutils import build_ext as build_ext_c
    cython=True
except Exception:
    cython=False
    suffix = '.c'
    cmdclass['build_ext'] = CheckingBuildExt
    
    class MissingCython(Command):
        
        user_options = []
        
        def initialize_options(self):
            pass
        
        def finalize_options(self):
            pass
        
        def run(self):
            try:
                import Cython
            except ImportError:
                warn("Cython is missing")
            else:
                cv = getattr(Cython, "__version__", None)
                if cv is None or V(cv) < V('0.16'):
                    warn(
                        "Cython >= 0.16 is required for compiling Cython sources, "
                        "found: %s" % (cv or "super old")
                    )
    cmdclass['cython'] = MissingCython
else:
    
    suffix = '.pyx'
    
    class CythonCommand(build_ext_c):
        """Custom distutils command subclassed from Cython.Distutils.build_ext
        to compile pyx->c, and stop there. All this does is override the 
        C-compile method build_extension() with a no-op."""
        
        description = "Compile Cython sources to C"
        
        def build_extension(self, ext):
            pass
    
    class zbuild_ext(build_ext_c):
        
        def build_extensions(self):
            if self.compiler.compiler_type == 'mingw32':
                customize_mingw(self.compiler)
            return build_ext_c.build_extensions(self)
        
        def run(self):
            self.distribution.run_command('configure')
            return build_ext.run(self)
    
    cmdclass['cython'] = CythonCommand
    cmdclass['build_ext'] =  zbuild_ext

extensions = []
for submod, packages in submodules.items():
    for pkg in sorted(packages):
        sources = [pjoin('zmq', submod.replace('.', os.path.sep), pkg+suffix)]
        if suffix == '.pyx':
            sources.extend(packages[pkg])
        ext = Extension(
            'zmq.%s.%s'%(submod, pkg),
            sources = sources,
            include_dirs=[pjoin('zmq', sub) for sub in ('utils',pjoin('backend', 'cython'),'devices')],
        )
        if suffix == '.pyx' and ext.sources[0].endswith('.c'):
            # undo setuptools stupidly clobbering cython sources:
            ext.sources = sources
        extensions.append(ext)

if 'PyPy' in sys.version:
    try:
        from zmq.backend.cffi import ffi
    except ImportError:
        warn("Couldn't get CFFI extension")
        extensions = []
    else:
        extensions = [ffi.verifier.get_extension()]

package_data = {'zmq':['*.pxd'],
                'zmq.backend.cython':['*.pxd'],
                'zmq.devices':['*.pxd'],
                'zmq.utils':['*.pxd', '*.h'],
}

package_data['zmq'].append('libzmq'+lib_ext)

def extract_version():
    """extract pyzmq version from sugar/version.py, so it's not multiply defined"""
    with open(pjoin('zmq', 'sugar', 'version.py')) as f:
        while True:
            line = f.readline()
            if line.startswith('# Code'):
                lines = []
                while line and not line.startswith('def'):
                    lines.append(line)
                    line = f.readline()
                break
    exec(''.join(lines), globals())
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
PyZMQ is the official Python binding for the ZeroMQ Messaging Library (http://www.zeromq.org).
"""

setup_args = dict(
    name = "pyzmq",
    version = extract_version(),
    packages = find_packages(),
    ext_modules = extensions,
    package_data = package_data,
    author = "Brian E. Granger, Min Ragan-Kelley",
    author_email = "zeromq-dev@lists.zeromq.org",
    url = 'http://github.com/zeromq/pyzmq',
    download_url = 'http://github.com/zeromq/pyzmq/releases',
    description = "Python bindings for 0MQ",
    long_description = long_desc, 
    license = "LGPL+BSD",
    cmdclass = cmdclass,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
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
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
)
if 'setuptools' in sys.modules and 'PyPy' in sys.version:
    setup_args['install_requires'] = [
        'py',
        'cffi',
    ]

setup(**setup_args)

