"""misc build utility functions"""

# Copyright (c) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import os
import sys
import logging
from distutils import ccompiler
from distutils.sysconfig import customize_compiler
from pipes import quote
from subprocess import Popen, PIPE

pjoin = os.path.join


if sys.version_info[0] >= 3:
    u = lambda x: x
else:
    u = lambda x: x.decode('utf8', 'replace')


def customize_mingw(cc):
    # strip -mno-cygwin from mingw32 (Python Issue #12641)
    for cmd in [cc.compiler, cc.compiler_cxx, cc.compiler_so, cc.linker_exe, cc.linker_so]:
        if '-mno-cygwin' in cmd:
            cmd.remove('-mno-cygwin')
    
    # remove problematic msvcr90
    if 'msvcr90' in cc.dll_libraries:
        cc.dll_libraries.remove('msvcr90')


def get_compiler(compiler, **compiler_attrs):
    """get and customize a compiler"""
    if compiler is None or isinstance(compiler, str):
        cc = ccompiler.new_compiler(compiler=compiler)
        customize_compiler(cc)
        if cc.compiler_type == 'mingw32':
            customize_mingw(cc)
    else:
        cc = compiler
    
    for name, val in compiler_attrs.items():
        setattr(cc, name, val)
    
    return cc


def get_output_error(cmd):
    """Return the exit status, stdout, stderr of a command"""
    if not isinstance(cmd, list):
        cmd = [cmd]
    logging.debug("Running: %s", ' '.join(map(quote, cmd)))
    try:
        result = Popen(cmd, stdout=PIPE, stderr=PIPE)
    except IOError as e:
        return -1, u(''), u('Failed to run %r: %r' % (cmd, e))
    so, se = result.communicate()
    # unicode:
    so = so.decode('utf8', 'replace')
    se = se.decode('utf8', 'replace')
    
    return result.returncode, so, se

