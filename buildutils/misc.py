"""misc build utility functions"""

# Copyright (c) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import copy
import logging
import os
import sys
from pprint import pprint
from shlex import quote
from subprocess import PIPE, Popen

from .msg import warn

pjoin = os.path.join


def customize_mingw(cc):
    # strip -mno-cygwin from mingw32 (Python Issue #12641)
    for cmd in [
        cc.compiler,
        cc.compiler_cxx,
        cc.compiler_so,
        cc.linker_exe,
        cc.linker_so,
    ]:
        if '-mno-cygwin' in cmd:
            cmd.remove('-mno-cygwin')

    # remove problematic msvcr90
    if 'msvcr90' in cc.dll_libraries:
        cc.dll_libraries.remove('msvcr90')


def get_compiler(compiler, **compiler_attrs):
    """get and customize a compiler"""
    cc = copy.deepcopy(compiler)

    for name, val in compiler_attrs.items():
        setattr(cc, name, val)

    return cc


def get_output_error(cmd, **kwargs):
    """Return the exit status, stdout, stderr of a command"""
    if not isinstance(cmd, list):
        cmd = [cmd]
    logging.debug("Running: %s", ' '.join(map(quote, cmd)))
    try:
        result = Popen(cmd, stdout=PIPE, stderr=PIPE, **kwargs)
    except OSError as e:
        return -1, '', f'Failed to run {cmd!r}: {e!r}'
    so, se = result.communicate()
    # unicode:
    so = so.decode('utf8', 'replace')
    se = se.decode('utf8', 'replace')

    return result.returncode, so, se


def locate_vcredist_dir(plat):
    """Locate vcredist directory and add it to $PATH

    Adding it to $PATH is required to run
    executables that link libzmq to find e.g. msvcp140.dll
    """
    from setuptools import msvc

    vcvars = msvc.msvc14_get_vc_env(plat)
    try:
        vcruntime = vcvars["py_vcruntime_redist"]
    except KeyError:
        warn(f"platform={plat}, vcvars=")
        pprint(vcvars, stream=sys.stderr)

        warn(
            "Failed to get py_vcruntime_redist via vcvars, may need to set it in %PATH%"
        )
        return None
    redist_dir, dll = os.path.split(vcruntime)
    # add redist dir to $PATH so that it can be found
    os.environ["PATH"] += os.pathsep + redist_dir
    return redist_dir
