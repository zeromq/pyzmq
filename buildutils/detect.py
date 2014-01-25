"""Detect zmq version"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011-2014 Brian Granger, Min Ragan-Kelley, Pawel Jasinski
#
#  This file is part of pyzmq, copied and adapted from h5py.
#  h5py source used under the New BSD license
#
#  h5py: <http://code.google.com/p/h5py/>
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from __future__ import print_function

import shutil
import sys
import os
import logging
import platform
from glob import glob
from distutils import ccompiler
from distutils.sysconfig import customize_compiler
from subprocess import Popen, PIPE

from .misc import customize_mingw
from .msg import info, fatal

pjoin = os.path.join

#-----------------------------------------------------------------------------
# Utility functions (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------

def test_compilation(cfile, compiler=None, **compiler_attrs):
    """Test simple compilation with given settings"""
    if compiler is None or isinstance(compiler, str):
        cc = ccompiler.new_compiler(compiler=compiler)
        customize_compiler(cc)
        if cc.compiler_type == 'mingw32':
            customize_mingw(cc)
    else:
        cc = compiler
    
    for name, val in compiler_attrs.items():
        setattr(cc, name, val)
    
    efile, ext = os.path.splitext(cfile)

    cpreargs = lpreargs = None
    if sys.platform == 'darwin':
        # use appropriate arch for compiler
        if platform.architecture()[0]=='32bit':
            if platform.processor() == 'powerpc':
                cpu = 'ppc'
            else:
                cpu = 'i386'
            cpreargs = ['-arch', cpu]
            lpreargs = ['-arch', cpu, '-undefined', 'dynamic_lookup']
        else:
            # allow for missing UB arch, since it will still work:
            lpreargs = ['-undefined', 'dynamic_lookup']
    if sys.platform == 'sunos5':
        if platform.architecture()[0]=='32bit':
            lpreargs = ['-m32']
        else: 
            lpreargs = ['-m64']
    extra = compiler_attrs.get('extra_compile_args', None)

    objs = cc.compile([cfile],extra_preargs=cpreargs, extra_postargs=extra)
    cc.link_executable(objs, efile, extra_preargs=lpreargs)
    return efile

def compile_and_run(basedir, src, compiler=None, **compiler_attrs):
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    cfile = pjoin(basedir, os.path.basename(src))
    shutil.copy(src, cfile)
    try:
        efile = test_compilation(cfile, compiler=compiler, **compiler_attrs)
        result = Popen(efile, stdout=PIPE, stderr=PIPE)
        so, se = result.communicate()
        # for py3k:
        so = so.decode()
        se = se.decode()
    finally:
        shutil.rmtree(basedir)
    
    return result.returncode, so, se


def detect_zmq_compile(basedir, compiler=None, **compiler_attrs):
    """Compile, link & execute a test program, in empty directory `basedir`.
    
    The C compiler will be updated with any keywords given via setattr.
    
    Parameters
    ----------
    
    basedir : path
        The location where the test program will be compiled and run
    compiler : str
        The distutils compiler key (e.g. 'unix', 'msvc', or 'mingw32')
    **compiler_attrs : dict
        Any extra compiler attributes, which will be set via ``setattr(cc)``.
    
    Returns
    -------
    
    A dict of properties for zmq compilation, with the following two keys:
    
    vers : tuple
        The ZMQ version as a tuple of ints, e.g. (2,2,0)
    settings : dict
        The compiler options used to compile the test function, e.g. `include_dirs`,
        `library_dirs`, `libs`, etc.
    """
    
    cfile = pjoin(basedir, 'vers.c')
    shutil.copy(pjoin(os.path.dirname(__file__), 'vers.c'), cfile)
    
    # check if we need to link against Realtime Extensions library
    if sys.platform.startswith('linux'):
        cc = ccompiler.new_compiler(compiler=compiler)
        cc.output_dir = basedir
        if not cc.has_function('timer_create'):
            compiler_attrs['libraries'].append('rt')
            
    efile = test_compilation(cfile, compiler=compiler, **compiler_attrs)
    
    result = Popen(efile, stdout=PIPE, stderr=PIPE)
    so, se = result.communicate()
    # for py3k:
    so = so.decode()
    se = se.decode()
    if result.returncode:
        msg = "Error running version detection script:\n%s\n%s" % (so,se)
        logging.error(msg)
        raise IOError(msg)

    handlers = {'vers':  lambda val: tuple(int(v) for v in val.split('.'))}

    props = {}
    for line in (x for x in so.split('\n') if x):
        key, val = line.split(':')
        props[key] = handlers[key](val)

    return props

def is64bit():
    """
    returns true if running as ipy64.exe
    """
    if sys.platform == 'cli':
        import System
        return System.IntPtr.Size == 8
    else:
        raise NotImplementedError()

def pick_dll(path, visual_studio_version):
    """
    scans zmqlib location for libzmq.dll
    take into account libzmq-*.dll naming convention as described on:
    http://zeromq.org/distro:microsoft-windows
    returns: path to selected dll
    """
    # try to scan bin folder as it was installed with .msi
    pattern = pjoin(path, 'libzmq-%s*.dll' % visual_studio_version)
    candidates = glob(pattern)
    # get rid of debug versions
    for candidate in list(candidates):
        if -1 != candidate.find('gd'):
            candidates.remove(candidate)

    if len(candidates) > 0:
        if len(candidates) == 1:
            return candidates[0]
        # assume *not* xp, ironpython platform.win32_ver is broken
        for candidate in list(candidates):
            if -1 != candidate.find('xp'):
                candidates.remove(candidate)
        if len(candidates) == 1:
            return candidates[0]
        # more than one
        fatal('\n    '.join(['Unable to narrow down to one library, candidates are:'] + candidates ))

    # try to scan bin folder as it was build using visual studio
    # zmqlib/bin/Win32
    # zmqlib/bin/x64
    dll_name = pjoin(path, 'x64' if is64bit() else 'Win32', 'libzmq.dll')
    if os.path.exists(dll_name):
        return dll_name
    # last resort - zmqlib/bin
    dll_name = pjoin(path, 'libzmq.dll')
    if os.path.exists(dll_name):
        return dll_name

    fatal('\n    '.join(['Unable to locate any form of libzmq in specified location:', path]))

def detect_zmq_import(visual_studio_version, location):
    """
    based on location and visual studio versio, load library and read out version number

    Parameters
    ----------

    visual_studio_version : string
        version code as defined by: http://zeromq.org/distro:microsoft-windows
    location : string
        path to zmq location where libzmq can be found

    Returns
    -------

    A dict of properties with the following two keys:

    vers : tuple
        The ZMQ version as a tuple of ints, e.g. (2,2,0)
    dll_name : string
        The name of the selected library file.
    """
    dll_name = pick_dll(pjoin(location, 'bin'), visual_studio_version)
    import ctypes
    libzmq = ctypes.CDLL(dll_name, mode=ctypes.RTLD_GLOBAL)
    major = ctypes.c_int()
    minor = ctypes.c_int()
    patch = ctypes.c_int()
    libzmq.zmq_version(ctypes.byref(major), ctypes.byref(minor), ctypes.byref(patch))

    return { 'vers' : (major.value, minor.value, patch.value),
             'dll_name' : dll_name  }
