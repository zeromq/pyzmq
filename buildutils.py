"""Detect zmq version"""
#
#    Copyright (c) 2011 Min Ragan-Kelley
#
#    This file is part of pyzmq, copied and adapted from h5py.
#    h5py source used under the New BSD license
#
#    h5py: <http://code.google.com/p/h5py/>
#    BSD license: <http://www.opensource.org/licenses/bsd-license.php>
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

import shutil
import sys
import os
import logging
import pickle
from distutils import ccompiler
from subprocess import Popen, PIPE

try:
    from configparser import ConfigParser
except:
    from ConfigParser import ConfigParser

pjoin = os.path.join

#-----------------------------------------------------------------------------
# Logging (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stderr))

def debug(what):
    pass

def fatal(instring, code=1):
    logger.error("Fatal: "+instring)
    exit(code)

def warn(instring):
    logger.error("Warning: "+instring)


#-----------------------------------------------------------------------------
# Utility functions (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------

def detect_zmq(basedir, **compiler_attrs):
    """Compile, link & execute a test program, in empty directory `basedir`.
    
    The C compiler will be updated with any keywords given via setattr.
    
    Parameters
    ----------
    
    basedir : path
        The location where the test program will be compiled and run
    **compiler_attrs : dict
        Any extra compiler attributes, which will be set via ``setattr(cc)``.
    
    Returns
    -------
    
    A dict of properties for zmq compilation, with the following two keys:
    
    vers : tuple
        The ZMQ version as a tuple of ints, e.g. (2,2,0)
    options : dict
        The compiler options used to compile the test function, e.g. `include_dirs`,
        `library_dirs`, `libs`, etc.
    """

    cc = ccompiler.new_compiler()
    for name, val in compiler_attrs.items():
        setattr(cc, name, val)

    cfile = pjoin(basedir, 'vers.c')
    efile = pjoin(basedir, 'vers')

    f = open(cfile, 'w')
    try:
        f.write(
r"""
#include <stdio.h>
#include "zmq.h"

int main(){
    unsigned int major, minor, patch;
    zmq_version(&major, &minor, &patch);
    fprintf(stdout, "vers: %d.%d.%d\n", major, minor, patch);
    return 0;
}
""")
    finally:
        f.close()

    if sys.platform == 'darwin':
        # allow for missing UB arch, since it will still work:
        preargs = ['-undefined', 'dynamic_lookup']
    else:
        preargs = None

    objs = cc.compile([cfile])
    cc.link_executable(objs, efile, extra_preargs=preargs)

    result = Popen(efile, stdout=PIPE, stderr=PIPE)
    so, se = result.communicate()
    # for py3k:
    so = so.decode()
    se = se.decode()
    if result.returncode:
        msg = "Error running version detection script:\n%s\n%s" % (so,se)
        logging.error(msg)
        raise IOError(msg)

    handlers = {'vers':     lambda val: tuple(int(v) for v in val.split('.'))}

    props = {}
    for line in (x for x in so.split('\n') if x):
        key, val = line.split(':')
        props[key] = handlers[key](val)

    props['options'] = compiler_attrs
    return props

def localpath(*args):
    plist = [os.path.dirname(__file__)]+list(args)
    return os.path.abspath(pjoin(*plist))

def loadpickle(name):
    """ Load object from pickle file, or None if it can't be opened """
    name = pjoin('conf', name)
    try:
        f = open(name,'rb')
    except IOError:
        # raise
        return None
    try:
        return pickle.load(f)
    except Exception:
        # raise
        return None
    finally:
        f.close()

def savepickle(name, data):
    """ Save to pickle file, exiting if it can't be written """
    if not os.path.exists('conf'):
        os.mkdir('conf')
    name = pjoin('conf', name)
    try:
        f = open(name, 'wb')
    except IOError:
        fatal("Can't open pickle file \"%s\" for writing" % name)
    try:
        pickle.dump(data, f, 0)
    finally:
        f.close()

def v_str(v_tuple):
    """turn (2,0,1) into '2.0.1'."""
    return ".".join(str(x) for x in v_tuple)

def get_eargs():
    """ Look for options in environment vars """

    settings = {}

    zmq = os.environ.get("ZMQ_DIR", '')
    if zmq != '':
        debug("Found environ var ZMQ_DIR=%s" % zmq)
        settings['zmq'] = zmq

    return settings

def get_cfg_args():
    """ Look for options in setup.cfg """

    settings = {}
    zmq = ''
    if not os.path.exists('setup.cfg'):
        return settings
    cfg = ConfigParser()
    cfg.read('setup.cfg')
    if 'build_ext' in cfg.sections() and \
                cfg.has_option('build_ext', 'include_dirs'):
        includes = cfg.get('build_ext', 'include_dirs')
        include = includes.split(os.pathsep)[0]
        if include.endswith('include') and os.path.isdir(include):
            zmq = include[:-8]
    if zmq != '':
        debug("Found ZMQ=%s in setup.cfg" % zmq)
        settings['zmq'] = zmq

    return settings

def get_cargs():
    """ Look for global options in the command line """
    settings = loadpickle('buildconf.pickle')
    if settings is None:  settings = {}
    for arg in sys.argv[:]:
        if arg.find('--zmq=') == 0:
            zmq = arg.split('=')[-1]
            if zmq.lower() == 'default':
                settings.pop('zmq', None)
            else:
                settings['zmq'] = zmq
            sys.argv.remove(arg)
    savepickle('buildconf.pickle', settings)
    return settings

def discover_settings():
    """ Discover custom settings for ZMQ path"""
    settings = get_cfg_args()       # lowest priority
    settings.update(get_eargs())
    settings.update(get_cargs())    # highest priority
    return settings.get('zmq')

def copy_and_patch_libzmq(ZMQ, libzmq):
    """copy libzmq into source dir, and patch it if necessary.
    
    This command is necessary prior to running a bdist on Linux or OS X.
    """
    if sys.platform.startswith('win'):
        return
    # copy libzmq into zmq for bdist
    local = localpath('zmq',libzmq)
    if ZMQ is None and not os.path.exists(local):
        fatal("Please specify zmq prefix via `setup.py configure --zmq=/path/to/zmq` "
        "or copy libzmq into zmq/ manually prior to running bdist.")
    try:
        lib = pjoin(ZMQ, 'lib', libzmq)
        print ("copying %s -> %s"%(lib, local))
        shutil.copy(lib, local)
    except Exception:
        if not os.path.exists(local):
            fatal("Could not copy libzmq into zmq/, which is necessary for bdist. "
            "Please specify zmq prefix via `setup.py configure --zmq=/path/to/zmq` "
            "or copy libzmq into zmq/ manually.")
    finally:
        # link libzmq.dylib -> libzmq.1.dylib
        link = localpath('zmq',libzmq.replace('.1',''))
        if not os.path.exists(link):
            os.symlink(libzmq, link)
    
    if sys.platform == 'darwin':
        # patch install_name on darwin, instead of using rpath
        cmd = ['install_name_tool', '-id', '@loader_path/../%s'%libzmq, local]
        try:
            p = Popen(cmd, stdout=PIPE,stderr=PIPE)
        except OSError:
            fatal("install_name_tool not found, cannot patch libzmq for bundling.")
        out,err = p.communicate()
        if p.returncode:
            fatal("Could not patch bundled libzmq install_name: %s"%err, p.returncode)
        
