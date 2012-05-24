"""utilities for fetching build dependencies."""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012 Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#
#  This bundling code is largely adapted from pyzmq-static's get.sh by
#  Brandon Craig-Rhodes, which is itself BSD licensed.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import shutil
import sys
import tarfile
from subprocess import Popen, PIPE

try:
    # py2
    from urllib2 import urlopen
except ImportError:
    # py3
    from urllib.request import urlopen

from .msg import fatal, debug, info, warn

pjoin = os.path.join

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

bundled_version = (2,2,0)
libzmq = "zeromq-%i.%i.%i.tar.gz" % (bundled_version)
libzmq_url = "http://download.zeromq.org/" + libzmq
util = "util-linux-2.21.tar.gz"
util_url = "http://www.kernel.org/pub/linux/utils/util-linux/v2.21/" + util

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)

#-----------------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------------


def untgz(archive):
    return archive.replace('.tar.gz', '')

def localpath(*args):
    """construct an absolute path from a list relative to the root pyzmq directory"""
    plist = [ROOT] + list(args)
    return os.path.abspath(pjoin(*plist))

def fetch_archive(savedir, url, fname, force=False):
    """download an archive to a specific location"""
    dest = pjoin(savedir, fname)
    if os.path.exists(dest) and not force:
        info("already have %s" % fname)
        return dest
    info("fetching %s into %s" % (url, savedir))
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    req = urlopen(url)
    with open(dest, 'wb') as f:
        f.write(req.read())
    return dest

def fetch_libzmq(savedir):
    """download and extract libzmq"""
    dest = pjoin(savedir, 'zeromq')
    if os.path.exists(dest):
        info("already have %s" % dest)
        return
    fname = fetch_archive(savedir, libzmq_url, libzmq)
    tf = tarfile.open(fname)
    with_version = pjoin(savedir, tf.firstmember.path)
    tf.extractall(savedir)
    tf.close()
    # remove version suffix:
    shutil.move(with_version, dest)

def stage_platform_hpp(zmqroot):
    """stage platform.hpp into libzmq sources
    
    Tries ./configure first (except on Windows),
    then falls back on included platform.hpp previously generated.
    """
    
    platform_hpp = pjoin(zmqroot, 'src', 'platform.hpp')
    if os.path.exists(platform_hpp):
        info("already have platform.hpp")
        return
    if os.name == 'nt':
        # stage msvc platform header
        platform_dir = pjoin(zmqroot, 'builds', 'msvc')
    else:
        info("attempting ./configure to generate platform.hpp")
        
        p = Popen('./configure', cwd=zmqroot, shell=True,
            stdout=PIPE, stderr=PIPE,
        )
        o,e = p.communicate()
        if p.returncode:
            warn("failed to configure libzmq:\n%s" % e)
            if sys.platform == 'darwin':
                platform_dir = pjoin(HERE, 'include_darwin')
            elif sys.platform.startswith('freebsd'):
                platform_dir = pjoin(HERE, 'include_freebsd')
            else:
                platform_dir = pjoin(HERE, 'include_linux')
        else:
            return
    
    info("staging platform.hpp from: %s" % platform_dir)
    shutil.copy(pjoin(platform_dir, 'platform.hpp'), platform_hpp)


def fetch_uuid(savedir):
    """download, extract, and patch libuuid sources"""
    dest = pjoin(savedir, 'uuid')
    if os.path.exists(dest):
        info("already have %s" % dest)
        return
    
    fname = fetch_archive(savedir, util_url, util)
    tf = tarfile.open(fname)
    util_name = untgz(util)
    uuid_path = util_name+'/libuuid/src'
    uuid = filter(
        lambda m: m.name.startswith(uuid_path) and not m.name.endswith("nt.c"),
        tf.getmembers()
    )
    # uuid_members = map(tf.getmember, uuid_names)
    tf.extractall(savedir, uuid)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.move(pjoin(savedir, util_name, 'libuuid', 'src'), dest)
    shutil.rmtree(pjoin(savedir, util_name))
    
    patch_uuid(dest)


def patch_uuid(uuid_dir):
    """patch uuid.h with a few defines
    
    from pyzmq-static
    """
    info("patching gen_uuid.c")
    gen_uuid = pjoin(uuid_dir, "gen_uuid.c")
    with open(gen_uuid) as f:
        lines = f.readlines()
    
    if 'pyzmq-patch' in lines[0]:
        info("already patched")
        return
    else:
        lines.insert(0, "// end pyzmq-patch\n")
        for h in ('UNISTD', 'STDLIB', 'SYS_FILE'):
            lines.insert(0, "#define HAVE_%s_H\n" % h)
        lines.insert(0, "// begin pyzmq-patch\n")

    with open(gen_uuid, 'w') as f:
        f.writelines(lines)
    


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
        # resolve real file through symlinks
        lib = os.path.realpath(pjoin(ZMQ, 'lib', libzmq))
        print ("copying %s -> %s"%(lib, local))
        shutil.copy(lib, local)
    except Exception:
        if not os.path.exists(local):
            fatal("Could not copy libzmq into zmq/, which is necessary for bdist. "
            "Please specify zmq prefix via `setup.py configure --zmq=/path/to/zmq` "
            "or copy libzmq into zmq/ manually.")
    
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
        
