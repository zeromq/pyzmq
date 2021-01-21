"""Detect zmq version"""
# -----------------------------------------------------------------------------
#  Copyright (C) PyZMQ Developers
#
#  This file is part of pyzmq, copied and adapted from h5py.
#  h5py source used under the New BSD license
#
#  h5py: <http://code.google.com/p/h5py/>
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
# -----------------------------------------------------------------------------

import shutil
import sys
import os
import logging
import platform
from distutils import ccompiler
from distutils.sysconfig import customize_compiler

from .misc import get_compiler, get_output_error
from .msg import info
from .patch import patch_lib_paths

pjoin = os.path.join

# -----------------------------------------------------------------------------
# Utility functions (adapted from h5py: https://www.h5py.org/)
# -----------------------------------------------------------------------------


def test_compilation(cfile, compiler=None, **compiler_attrs):
    """Test simple compilation with given settings"""
    cc = get_compiler(compiler, **compiler_attrs)

    efile, ext = os.path.splitext(cfile)

    cpreargs = lpreargs = []
    if sys.platform == 'darwin':
        # use appropriate arch for compiler
        if platform.architecture()[0] == '32bit':
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
        if platform.architecture()[0] == '32bit':
            lpreargs = ['-m32']
        else:
            lpreargs = ['-m64']
    extra = compiler_attrs.get('extra_compile_args', None)
    extra_link = compiler_attrs.get('extra_link_args', [])
    lpreargs.extend(extra_link)

    objs = cc.compile([cfile], extra_preargs=cpreargs, extra_postargs=extra)
    cc.link_executable(objs, efile, extra_preargs=lpreargs)
    return efile


def compile_and_forget(basedir, src, compiler=None, **compiler_attrs):
    """Make sure src compiles and links successfully.

    The resulting binary is deleted without being run.
    """
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    cfile = pjoin(basedir, os.path.basename(src))
    shutil.copy(src, cfile)
    try:
        cc = get_compiler(compiler, **compiler_attrs)
        efile = test_compilation(cfile, compiler=cc, **compiler_attrs)
    finally:
        shutil.rmtree(basedir)


def detect_zmq(basedir, compiler=None, **compiler_attrs):
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
        customize_compiler(cc)
        cc.output_dir = basedir
        info("Checking for timer_create")
        info(
            "** Errors about missing timer_create are a normal part of this process **"
        )
        if not cc.has_function('timer_create'):
            compiler_attrs['libraries'].append('rt')
            info(
                "** The above error about timer_create is normal and not a problem! **"
            )
            info("no timer_create, linking librt")

    cc = get_compiler(compiler=compiler, **compiler_attrs)
    efile = test_compilation(cfile, compiler=cc, **compiler_attrs)
    patch_lib_paths(efile, cc.library_dirs)

    # add library dirs to %PATH% for windows
    env = os.environ.copy()
    if sys.platform.startswith("win"):
        env["PATH"] = os.pathsep.join([env["PATH"]] + cc.library_dirs)

    rc, so, se = get_output_error([efile], env=env)
    if rc:
        msg = "Error running version detection script:\n%s\n%s" % (so, se)
        logging.error(msg)
        raise IOError(msg)

    handlers = {'vers': lambda val: tuple(int(v) for v in val.split('.'))}

    props = {}
    for line in (x for x in so.split('\n') if x):
        key, val = line.split(':')
        props[key] = handlers[key](val)

    return props
