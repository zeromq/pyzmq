#!/usr/bin/env python
#-----------------------------------------------------------------------------
#  Copyright (C) PyZMQ Developers
#  Distributed under the terms of the Modified BSD License.
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

from __future__ import with_statement, print_function

import copy
import os
import shutil
import subprocess
import sys
import time
import errno
import platform
from traceback import print_exc

# whether any kind of bdist is happening
# do this before importing anything from distutils
doing_bdist = any(arg.startswith('bdist') for arg in sys.argv[1:])

if any(bdist in sys.argv for bdist in ['bdist_wheel', 'bdist_egg']):
    import setuptools

import distutils
from distutils.core import setup, Command
from distutils.ccompiler import get_default_compiler
from distutils.ccompiler import new_compiler
from distutils.extension import Extension
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist
from distutils.version import LooseVersion as V

from glob import glob
from os.path import splitext, basename, join as pjoin

from subprocess import Popen, PIPE, check_call, CalledProcessError

# local script imports:
from buildutils import (
    discover_settings, v_str, save_config, detect_zmq, merge,
    config_from_prefix,
    info, warn, fatal, debug, line, copy_and_patch_libzmq, localpath,
    fetch_libzmq, stage_platform_hpp,
    bundled_version, customize_mingw,
    compile_and_run,
    patch_lib_paths,
    )

# name of the libzmq library - can be changed by --libzmq <name>
libzmq_name = 'libzmq'

#-----------------------------------------------------------------------------
# Flags
#-----------------------------------------------------------------------------

pypy = 'PyPy' in sys.version

# reference points for zmq compatibility

min_legacy_zmq = (2,1,4)
min_good_zmq = (3,2)
target_zmq = bundled_version
dev_zmq = (target_zmq[0], target_zmq[1] + 1, 0)

# set dylib ext:
if sys.platform.startswith('win'):
    lib_ext = '.dll'
elif sys.platform == 'darwin':
    lib_ext = '.dylib'
else:
    lib_ext = '.so'

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

for idx, arg in enumerate(list(sys.argv)):
    if arg.startswith('--libzmq='):
        sys.argv.pop(idx)
        libzmq_name = arg.split("=",1)[1]
        break

#-----------------------------------------------------------------------------
# Configuration (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------

# --- compiler settings -------------------------------------------------

def bundled_settings(debug):
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
        temp = 'temp.%s-%i.%i' % (plat, sys.version_info[0], sys.version_info[1])
        suffix = ''
        if sys.version_info >= (3,5):
            # Python 3.5 adds EXT_SUFFIX to libs
            ext_suffix = distutils.sysconfig.get_config_var('EXT_SUFFIX')
            suffix = os.path.splitext(ext_suffix)[0]

        if debug:
            suffix = '_d' + suffix
            release = 'Debug'
        else:
            release = 'Release'

        settings['libraries'].append(libzmq_name + suffix)
        settings['library_dirs'].append(pjoin('build', temp, release, 'buildutils'))

    return settings

def check_pkgconfig():
    """ pull compile / link flags from pkg-config if present. """
    pcfg = None
    zmq_config = None
    try:
        check_call(['pkg-config', '--exists', 'libzmq'])
        # this would arguably be better with --variable=libdir /
        # --variable=includedir, but would require multiple calls
        pcfg = Popen(['pkg-config', '--libs', '--cflags', 'libzmq'],
                     stdout=subprocess.PIPE)
    except OSError as osexception:
        if osexception.errno == errno.ENOENT:
            info('pkg-config not found')
        else:
            warn("Running pkg-config failed - %s." % osexception)
    except CalledProcessError:
        info("Did not find libzmq via pkg-config.")

    if pcfg is not None:
        output, _ = pcfg.communicate()
        output = output.decode('utf8', 'replace')
        bits = output.strip().split()
        zmq_config = {'library_dirs':[], 'include_dirs':[], 'libraries':[]}
        for tok in bits:
            if tok.startswith("-L"):
                zmq_config['library_dirs'].append(tok[2:])
            if tok.startswith("-I"):
                zmq_config['include_dirs'].append(tok[2:])
            if tok.startswith("-l"):
                zmq_config['libraries'].append(tok[2:])
        info("Settings obtained from pkg-config: %r" % zmq_config)

    return zmq_config

def settings_from_prefix(prefix=None, bundle_libzmq_dylib=False):
    """load appropriate library/include settings from ZMQ prefix"""
    settings = {}
    settings['libraries'] = []
    settings['include_dirs'] = []
    settings['library_dirs'] = []
    settings['runtime_library_dirs'] = []
    settings['extra_link_args'] = [] 
    
    if sys.platform.startswith('win'):
        settings['libraries'].append(libzmq_name)
        
        if prefix:
            settings['include_dirs'] += [pjoin(prefix, 'include')]
            settings['library_dirs'] += [pjoin(prefix, 'lib')]
    else:
        # add pthread on freebsd
        if sys.platform.startswith('freebsd'):
            settings['libraries'].append('pthread')

        if sys.platform.startswith('sunos'):
          if platform.architecture()[0] == '32bit':
            settings['extra_link_args'] += ['-m32']
          else:
            settings['extra_link_args'] += ['-m64']

        if prefix:
            settings['libraries'].append('zmq')

            settings['include_dirs'] += [pjoin(prefix, 'include')]
            if not bundle_libzmq_dylib:
                if sys.platform.startswith('sunos') and platform.architecture()[0] == '64bit':
                    settings['library_dirs'] += [pjoin(prefix, 'lib/amd64')]
                settings['library_dirs'] += [pjoin(prefix, 'lib')]
        else:
            # If prefix is not explicitly set, pull it from pkg-config by default.
            # this is probably applicable across platforms, but i don't have
            # sufficient test environments to confirm
            pkgcfginfo = check_pkgconfig()
            if pkgcfginfo is not None:
                # we can get all the zmq-specific values from pkgconfg
                for key, value in pkgcfginfo.items():
                    settings[key].extend(value)
            else:
                settings['libraries'].append('zmq')

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
            info("%r" % settings)
            settings['runtime_library_dirs'] += [
                os.path.abspath(x) for x in settings['library_dirs']
            ]
    
    return settings

class LibZMQVersionError(Exception):
    pass

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
        # write to zmq.utils.[name].json
        save_config(name, cfg, os.path.join('zmq', 'utils'))
        # also write to build_lib, because we might be run after copying to
        # build_lib has already happened.
        build_lib_utils = os.path.join(self.build_lib, 'zmq', 'utils')
        if os.path.exists(build_lib_utils):
            save_config(name, cfg, build_lib_utils)
    
    def init_settings_from_config(self):
        """set up compiler settings, based on config"""
        cfg = self.config

        if sys.platform == 'win32' and cfg.get('bundle_msvcp') is None:
            # default bundle_msvcp=True on:
            # Windows Python 3.5 bdist *without* DISTUTILS_USE_SDK
            if os.environ.get("PYZMQ_BUNDLE_CRT") or (
                sys.version_info >= (3,5)
                and self.compiler_type == 'msvc'
                and not os.environ.get('DISTUTILS_USE_SDK')
                and doing_bdist
            ):
                cfg['bundle_msvcp'] = True

        if cfg['libzmq_extension']:
            settings = bundled_settings(self.debug)
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
        if sys.platform.startswith('win') and sys.version_info < (3, 3):
            settings['include_dirs'].insert(0, pjoin('buildutils', 'include_win32'))
        
        for ext in self.distribution.ext_modules:
            if ext.name.startswith('zmq.lib'):
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
            local_dll = pjoin(self.tempdir, libzmq_name + '.dll')
            if not self.config['zmq_prefix'] and not os.path.exists(local_dll):
                fatal("ZMQ directory must be specified on Windows via setup.cfg"
                " or 'python setup.py configure --zmq=/path/to/zeromq2'")
            
            try:
                shutil.copy(pjoin(self.config['zmq_prefix'], 'lib', libzmq_name + '.dll'), local_dll)
            except Exception:
                if not os.path.exists(local_dll):
                    warn("Could not copy " + libzmq_name + " into zmq/, which is usually necessary on Windows."
                    "Please specify zmq prefix via configure --zmq=/path/to/zmq or copy "
                    + libzmq_name + " into zmq/ manually.")

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
        else:
            return False

    def check_zmq_version(self):
        """check the zmq version"""
        cfg = self.config
        # build test program
        zmq_prefix = cfg['zmq_prefix']
        detected = self.test_build(zmq_prefix, self.compiler_settings)
        # now check the libzmq version
        
        vers = tuple(detected['vers'])
        vs = v_str(vers)
        if cfg['allow_legacy_libzmq']:
            min_zmq = min_legacy_zmq
        else:
            min_zmq = min_good_zmq
        if vers < min_zmq:
            msg = [
                "Detected ZMQ version: %s, but require ZMQ >= %s" % (vs, v_str(min_zmq)),
            ]
            if zmq_prefix:
                msg.append("    ZMQ_PREFIX=%s" % zmq_prefix)
            if vers >= min_legacy_zmq:
                
                msg.append("    Explicitly allow legacy zmq by specifying `--zmq=/zmq/prefix`")
            
            raise LibZMQVersionError('\n'.join(msg))
        if vers < min_good_zmq:
            msg = [
                "Detected legacy ZMQ version: %s. It is STRONGLY recommended to use ZMQ >= %s" % (vs, v_str(min_good_zmq)),
            ]
            if zmq_prefix:
                msg.append("    ZMQ_PREFIX=%s" % zmq_prefix)
            warn('\n'.join(msg))
        elif vers < target_zmq:
            warn("Detected ZMQ version: %s, but pyzmq targets ZMQ %s." % (
                    vs, v_str(target_zmq))
            )
            warn("libzmq features and fixes introduced after %s will be unavailable." % vs)
            line()
        elif vers >= dev_zmq:
            warn("Detected ZMQ version: %s. Some new features in libzmq may not be exposed by pyzmq." % vs)
            line()

        if sys.platform.startswith('win'):
            # fetch libzmq.dll into local dir
            local_dll = localpath('zmq', libzmq_name + '.dll')
            if not zmq_prefix and not os.path.exists(local_dll):
                fatal("ZMQ directory must be specified on Windows via setup.cfg or 'python setup.py configure --zmq=/path/to/zeromq2'")
            try:
                shutil.copy(pjoin(zmq_prefix, 'lib', libzmq_name + '.dll'), local_dll)
            except Exception:
                if not os.path.exists(local_dll):
                    warn("Could not copy " + libzmq_name + " into zmq/, which is usually necessary on Windows."
                    "Please specify zmq prefix via configure --zmq=/path/to/zmq or copy "
                    + libzmq_name + " into zmq/ manually.")
    
    def bundle_libzmq_extension(self):
        bundledir = "bundled"
        ext_modules = self.distribution.ext_modules
        if ext_modules and any(m.name == 'zmq.libzmq' for m in ext_modules):
            # I've already been run
            return
        
        line()
        info("Using bundled libzmq")
        
        # fetch sources for libzmq extension:
        if not os.path.exists(bundledir):
            os.makedirs(bundledir)
        
        fetch_libzmq(bundledir)
        
        stage_platform_hpp(pjoin(bundledir, 'zeromq'))

        sources = [pjoin('buildutils', 'initlibzmq.c')]
        sources += glob(pjoin(bundledir, 'zeromq', 'src', '*.cpp'))

        includes = [
            pjoin(bundledir, 'zeromq', 'include')
        ]

        if bundled_version < (4, 2, 0):
            tweetnacl = pjoin(bundledir, 'zeromq', 'tweetnacl')
            tweetnacl_sources = glob(pjoin(tweetnacl, 'src', '*.c'))

            randombytes = pjoin(tweetnacl, 'contrib', 'randombytes')
            if sys.platform.startswith('win'):
                tweetnacl_sources.append(pjoin(randombytes, 'winrandom.c'))
            else:
                tweetnacl_sources.append(pjoin(randombytes, 'devurandom.c'))

            sources += tweetnacl_sources
            includes.append(pjoin(tweetnacl, 'src'))
            includes.append(randombytes)
        else:
            # >= 4.2
            sources += glob(pjoin(bundledir, 'zeromq', 'src', 'tweetnacl.c'))

        # construct the Extensions:
        libzmq = Extension(
            'zmq.libzmq',
            sources=sources,
            include_dirs=includes,
        )
        
        # register the extension:
        self.distribution.ext_modules.insert(0, libzmq)
        
        # use tweetnacl to provide CURVE support
        libzmq.define_macros.append(('ZMQ_HAVE_CURVE', 1))
        libzmq.define_macros.append(('ZMQ_USE_TWEETNACL', 1))
        
        # select polling subsystem based on platform
        if sys.platform  == 'darwin' or 'bsd' in sys.platform:
            libzmq.define_macros.append(('ZMQ_USE_KQUEUE', 1))
        elif 'linux' in sys.platform:
            libzmq.define_macros.append(('ZMQ_USE_EPOLL', 1))
        elif sys.platform.startswith('win'):
            libzmq.define_macros.append(('ZMQ_USE_SELECT', 1))
        else:
            # this may not be sufficiently precise
            libzmq.define_macros.append(('ZMQ_USE_POLL', 1))
        
        if sys.platform.startswith('win'):
            # include defines from zeromq msvc project:
            libzmq.define_macros.append(('FD_SETSIZE', 16384))
            libzmq.define_macros.append(('DLL_EXPORT', 1))
            libzmq.define_macros.append(('_CRT_SECURE_NO_WARNINGS', 1))
            
            # When compiling the C++ code inside of libzmq itself, we want to
            # avoid "warning C4530: C++ exception handler used, but unwind
            # semantics are not enabled. Specify /EHsc".
            if self.compiler_type == 'msvc':
                libzmq.extra_compile_args.append('/EHsc')
            elif self.compiler_type == 'mingw32':
                libzmq.define_macros.append(('ZMQ_HAVE_MINGW32', 1))

            # And things like sockets come from libraries that must be named.
            libzmq.libraries.extend(['rpcrt4', 'ws2_32', 'advapi32'])
            
            # bundle MSCVP redist
            if self.config['bundle_msvcp']:
                cc = new_compiler(compiler=self.compiler_type)
                cc.initialize()
                # get vc_redist location via private API
                try:
                    cc._vcruntime_redist
                except AttributeError:
                    # fatal error if env set, warn otherwise
                    msg = fatal if os.environ.get("PYZMQ_BUNDLE_CRT") else warn
                    msg("Failed to get cc._vcruntime via private API, not bundling CRT")
                if cc._vcruntime_redist:
                    redist_dir, dll = os.path.split(cc._vcruntime_redist)
                    to_bundle = [
                        pjoin(redist_dir, dll.replace('vcruntime', name))
                        for name in ('msvcp', 'concrt')
                    ]
                    for src in to_bundle:
                        dest = localpath('zmq', basename(src))
                        info("Copying %s -> %s" % (src, dest))
                        # copyfile to avoid permission issues
                        shutil.copyfile(src, dest)

        else:
            libzmq.include_dirs.append(bundledir)

            # check if we need to link against Realtime Extensions library
            cc = new_compiler(compiler=self.compiler_type)
            cc.output_dir = self.build_temp
            if not sys.platform.startswith(('darwin', 'freebsd')):
                line()
                info("checking for timer_create")
                if not cc.has_function('timer_create'):
                    info("no timer_create, linking librt")
                    libzmq.libraries.append('rt')
                else:
                    info("ok")
                
                if pypy:
                    # seem to need explicit libstdc++ on linux + pypy
                    # not sure why
                    libzmq.libraries.append("stdc++")
        
        # copy the header files to the source tree.
        bundledincludedir = pjoin('zmq', 'include')
        if not os.path.exists(bundledincludedir):
            os.makedirs(bundledincludedir)
        if not os.path.exists(pjoin(self.build_lib, bundledincludedir)):
            os.makedirs(pjoin(self.build_lib, bundledincludedir))
        
        for header in glob(pjoin(bundledir, 'zeromq', 'include', '*.h')):
            shutil.copyfile(header, pjoin(bundledincludedir, basename(header)))
            shutil.copyfile(header, pjoin(self.build_lib, bundledincludedir, basename(header)))
        
        # update other extensions, with bundled settings
        self.config['libzmq_extension'] = True
        self.init_settings_from_config()
        self.save_config('config', self.config)
        
    
    def fallback_on_bundled(self):
        """Couldn't build, fallback after waiting a while"""
        
        line()
        
        warn('\n'.join([
        "Couldn't find an acceptable libzmq on the system.",
        "",
        "If you expected pyzmq to link against an installed libzmq, please check to make sure:",
        "",
        "    * You have a C compiler installed",
        "    * A development version of Python is installed (including headers)",
        "    * A development version of ZMQ >= %s is installed (including headers)" % v_str(min_good_zmq),
        "    * If ZMQ is not in a default location, supply the argument --zmq=<path>",
        "    * If you did recently install ZMQ to a default location,",
        "      try rebuilding the ld cache with `sudo ldconfig`",
        "      or specify zmq's location with `--zmq=/usr/local`",
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
            copy_and_patch_libzmq(zmq_prefix, libzmq_name+lib_ext)
        
        # first try with given config or defaults
        try:
            self.check_zmq_version()
        except LibZMQVersionError as e:
            info("\nBad libzmq version: %s\n" % e)
        except Exception as e:
            # print the error as distutils would if we let it raise:
            info("\nerror: %s\n" % e)
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
            except LibZMQVersionError as e:
                info("\nBad libzmq version: %s\n" % e)
            except Exception as e:
                # print the error as distutils would if we let it raise:
                info("\nerror: %s\n" % e)
            else:
                # if we get here the second run succeeded, so we need to update compiler
                # settings for the extensions with /usr/local prefix
                self.finish_run()
                return
        
        # finally, fallback on bundled
        
        if cfg['no_libzmq_extension']:
            fatal("Falling back on bundled libzmq,"
            " but config has explicitly prohibited building the libzmq extension."
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
    
    def run(self):
        """Run the test suite with py.test"""
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
        p = Popen([sys.executable, '-m', 'pytest', '-v', os.path.join('zmq', 'tests')])
        p.wait()
        sys.exit(p.returncode)

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
        _clean_me = []
        _clean_trees = []
        
        for d in ('build', 'dist', 'conf'):
            if os.path.exists(d):
                _clean_trees.append(d)
        
        for root, dirs, files in os.walk('buildutils'):
            if any(root.startswith(pre) for pre in _clean_trees):
                continue
            for f in files:
                if os.path.splitext(f)[-1] == '.pyc':
                    _clean_me.append(pjoin(root, f))
            
            if '__pycache__' in dirs:
                _clean_trees.append(pjoin(root, '__pycache__'))

        for root, dirs, files in os.walk('zmq'):
            if any(root.startswith(pre) for pre in _clean_trees):
                continue
            
            for f in files:
                if os.path.splitext(f)[-1] in ('.pyc', '.so', '.o', '.pyd', '.json'):
                    _clean_me.append(pjoin(root, f))

            for d in dirs:
                if d == '__pycache__':
                    _clean_trees.append(pjoin(root, d))
        
        # remove generated cython files
        if self.all:
            for root, dirs, files in os.walk(pjoin('zmq', 'backend', 'cython')):
                 if os.path.splitext(f)[-1] == '.c':
                     _clean_me.append(pjoin(root, f))
        
        bundled = glob(pjoin('zmq', 'libzmq*'))
        _clean_me.extend([ b for b in bundled if b not in _clean_me ])
        
        bundled_headers = glob(pjoin('zmq', 'include', '*.h'))
        _clean_me.extend([ h for h in bundled_headers if h not in _clean_me])
        
        for clean_me in _clean_me:
            print("removing %s" % clean_me)
            try:
                os.unlink(clean_me)
            except Exception as e:
                print(e, file=sys.stderr)
        for clean_tree in _clean_trees:
            print("removing %s/" % clean_tree)
            try:
                shutil.rmtree(clean_tree)
            except Exception as e:
                print(e, file=sys.stderr)


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
                Cython >= %s is required to compile pyzmq from a development branch.
                Please install Cython or download a release package of pyzmq.
                """ % (src, min_cython_version))
    
    def build_extensions(self):
        self.check_cython_extensions(self.extensions)
        self.check_extensions_list(self.extensions)
        
        if self.compiler.compiler_type == 'mingw32':
            customize_mingw(self.compiler)
        
        for ext in self.extensions:
            self.build_extension(ext)
    
    def build_extension(self, ext):
        build_ext.build_extension(self, ext)
        ext_path = self.get_ext_fullpath(ext.name)
        patch_lib_paths(ext_path, self.compiler.library_dirs)
    
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
checkrc = pxd('backend', 'cython', 'checkrc')
monqueue = pxd('devices', 'monitoredqueue')

submodules = {
    'backend.cython' : {'constants': [libzmq, pxi('backend', 'cython', 'constants')],
            'error':[libzmq, checkrc],
            '_poll':[libzmq, socket, context, checkrc],
            'utils':[libzmq, checkrc],
            'context':[context, libzmq, checkrc],
            'message':[libzmq, buffers, message, checkrc],
            'socket':[context, message, socket, libzmq, buffers, checkrc],
            '_device':[libzmq, socket, context, checkrc],
            '_version':[libzmq],
    },
    'devices' : {
            'monitoredqueue':[buffers, libzmq, monqueue, socket, context, checkrc],
    },
}

min_cython_version = '0.20'
try:
    import Cython
    if V(Cython.__version__) < V(min_cython_version):
        raise ImportError("Cython >= %s required for cython build, found %s" % (
            min_cython_version, Cython.__version__))
    from Cython.Distutils import build_ext as build_ext_c
    from Cython.Distutils import Extension
    cython = True
except Exception:
    cython = False
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
                if cv is None or V(cv) < V(min_cython_version):
                    warn(
                        "Cython >= %s is required for compiling Cython sources, "
                        "found: %s" % (min_cython_version, cv or Cython)
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
        
        def build_extension(self, ext):
            build_ext_c.build_extension(self, ext)
            ext_path = self.get_ext_fullpath(ext.name)
            patch_lib_paths(ext_path, self.compiler.library_dirs)
        
        def run(self):
            self.distribution.run_command('configure')
            
            return build_ext_c.run(self)
    
    cmdclass['cython'] = CythonCommand
    cmdclass['build_ext'] =  zbuild_ext

extensions = []
ext_include_dirs = [pjoin('zmq', sub) for sub in ('utils',)]
ext_kwargs = {
    'include_dirs': ext_include_dirs,
}
if cython:
    # set binding so that compiled methods can be inspected
    ext_kwargs['cython_directives'] = {'binding': True}

for submod, packages in submodules.items():
    for pkg in sorted(packages):
        sources = [pjoin('zmq', submod.replace('.', os.path.sep), pkg+suffix)]
        ext = Extension(
            'zmq.%s.%s'%(submod, pkg),
            sources = sources,
            **ext_kwargs
        )
        extensions.append(ext)

if pypy:
    # add dummy extension, to ensure build_ext runs
    dummy_ext = Extension('dummy', sources=[])
    extensions = [dummy_ext]

    bld_ext = cmdclass['build_ext']
    class pypy_build_ext(bld_ext):
        """hack to build pypy extension only after building bundled libzmq
        
        otherwise it will fail when libzmq is bundled.
        """
        def build_extensions(self):
            self.extensions.remove(dummy_ext)
            bld_ext.build_extensions(self)
            # build ffi extension after bundled libzmq,
            # because it may depend on linking it
            if self.inplace:
                sys.path.insert(0, '')
            else:
                sys.path.insert(0, self.build_lib)
            try:
                from zmq.backend.cffi import ffi
            except ImportError as e:
                warn("Couldn't get CFFI extension: %s" % e)
            else:
                ext = ffi.verifier.get_extension()
                if not ext.name.startswith('zmq.'):
                    ext.name = 'zmq.backend.cffi.' + ext.name
                self.extensions.append(ext)
                self.build_extension(ext)
            finally:
                sys.path.pop(0)

    
    # How many build_ext subclasses is this? 5? Gross.
    cmdclass['build_ext'] = pypy_build_ext


package_data = {'zmq': ['*.pxd', '*' + lib_ext],
                'zmq.backend.cython': ['*.pxd', '*.pxi'],
                'zmq.backend.cffi': ['*.h', '*.c'],
                'zmq.devices': ['*.pxd'],
                'zmq.utils': ['*.pxd', '*.h', '*.json'],
}


def extract_version():
    """extract pyzmq version from sugar/version.py, so it's not multiply defined"""
    with open(pjoin('zmq', 'sugar', 'version.py')) as f:
        while True:
            line = f.readline()
            if line.startswith('VERSION'):
                lines = []
                while line and not line.startswith('def'):
                    lines.append(line)
                    line = f.readline()
                break
    ns = {}
    exec(''.join(lines), ns)
    return ns['__version__']

def find_packages():
    """adapted from IPython's setupbase.find_packages()"""
    packages = []
    for dir,subdirs,files in os.walk('zmq'):
        package = dir.replace(os.path.sep, '.')
        if '__init__.py' not in files:
            # not a package
            continue
        if sys.version_info < (3,3) and 'asyncio' in package and 'sdist' not in sys.argv:
            # Don't install asyncio packages on old Python
            # avoids issues with tools like compileall, pytest, etc.
            # that get confused by presence of Python 3-only sources,
            # even when they are never imported.
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
    url = 'https://pyzmq.readthedocs.org',
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
if 'setuptools' in sys.modules:
    setup_args['zip_safe'] = False
    if pypy:
        setup_args['install_requires'] = [
            'py',
            'cffi',
        ]

setup(**setup_args)

