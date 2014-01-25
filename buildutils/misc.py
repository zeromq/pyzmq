"""misc build utility functions"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2012-2014 Min Ragan-Kelley, Pawel Jasinski
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------
import sys
import os

from .msg import info

def customize_mingw(cc):
    # strip -mno-cygwin from mingw32 (Python Issue #12641)
    for cmd in [cc.compiler, cc.compiler_cxx, cc.compiler_so, cc.linker_exe, cc.linker_so]:
        if '-mno-cygwin' in cmd:
            cmd.remove('-mno-cygwin')
    
    # remove problematic msvcr90
    if 'msvcr90' in cc.dll_libraries:
        cc.dll_libraries.remove('msvcr90')

def is_win():
    # generalisation for cpython and ironpython under windows
    return sys.platform.startswith('win') or (sys.platform == 'cli' and os.name == 'nt')

def generate_const_values(zmq_prefix, verbose=False):
    # generate zmq/backend/ctypes/ZMQ.h
    from .h2py import main
    from StringIO import StringIO
    log = StringIO()
    header_file = os.path.join(zmq_prefix, 'include', 'zmq.h')
    main(["-o", "zmq/backend/ctypes", header_file], log=log)
    if verbose:
        info(log.getvalue())
    log.close()

def validate_and_map_vs_version(visual_studio_version):
    """
    Validate and map visual studio version parameter.
    Valid values are either:
    - common visual studio moniker, such as 2010 or 2012
    - zmq code as defined by: http://zeromq.org/distro:microsoft-windows (e.g. v110)

    Returns
    -------

    zmq code as defined by: http://zeromq.org/distro:microsoft-windows

    if validation fails, exception is raised.
    """
    vs_version_map = { '2008':'v90', '2010':'v100', '2012':'v110', '2013':'v120',
                       'v90' :'v90', 'v100':'v100', 'v110':'v110', 'v120':'v120' }
    version = vs_version_map.get(visual_studio_version, None)
    if version == None:
        raise Exception('Unable to recognize visual studio version: %s' % visual_studio_version)
    return version

def locate_installed_zmq_win():
    """
    scan registry entry for a location of the installed libzmq package
    select version with the highest number

    Returns
    -------
    path to the location or empty string nothing found

    """
    # TODO: scan, install and select on launch both 32 and 64 bit version of library
    # The selected version of libzmq matches ipy version (ipy.exe or ipy64.exe) run during setup.
    from Microsoft.Win32 import Registry
    installed = None
    miru = Registry.LocalMachine.OpenSubKey(r"SOFTWARE\Miru")
    if miru == None:
        return ''
    for name in miru.GetSubKeyNames():
        versions = []
        if name.lower().startswith('zeromq'):
            versions.append(name)
    if len(versions) == 0:
        return ''
    versions.sort()
    selected = versions[-1]
    product = miru.OpenSubKey(selected)
    path = product.GetValue(None)
    return path

__all__ = ['is_win', 'customize_mingw', 'generate_const_values', 'locate_installed_zmq_win',
           'validate_and_map_vs_version']
