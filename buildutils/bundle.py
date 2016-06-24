"""utilities for fetching build dependencies."""

#-----------------------------------------------------------------------------
#  Copyright (C) PyZMQ Developers
#  Distributed under the terms of the Modified BSD License.
#
#  This bundling code is largely adapted from pyzmq-static's get.sh by
#  Brandon Craig-Rhodes, which is itself BSD licensed.
#-----------------------------------------------------------------------------


import os
import shutil
import stat
import sys
import tarfile
import hashlib
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

bundled_version = (4,1,5)
vs = '%i.%i.%i' % bundled_version
libzmq = "zeromq-%s.tar.gz" % vs
libzmq_url = "https://github.com/zeromq/zeromq{major}-{minor}/releases/download/v{vs}/{libzmq}".format(
    major=bundled_version[0],
    minor=bundled_version[1],
    vs=vs,
    libzmq=libzmq,
)
libzmq_checksum = "sha256:04aac57f081ffa3a2ee5ed04887be9e205df3a7ddade0027460b8042432bdbcf"

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

def untgz(archive):
    return archive.replace('.tar.gz', '')

def localpath(*args):
    """construct an absolute path from a list relative to the root pyzmq directory"""
    plist = [ROOT] + list(args)
    return os.path.abspath(pjoin(*plist))

def checksum_file(scheme, path):
    """Return the checksum (hex digest) of a file"""
    h = getattr(hashlib, scheme)()
    
    with open(path, 'rb') as f:
        chunk = f.read(65535)
        while chunk:
            h.update(chunk)
            chunk = f.read(65535)
    return h.hexdigest()

def fetch_archive(savedir, url, fname, checksum, force=False):
    """download an archive to a specific location"""
    dest = pjoin(savedir, fname)
    scheme, digest_ref = checksum.split(':')
    
    if os.path.exists(dest) and not force:
        info("already have %s" % dest)
        digest = checksum_file(scheme, fname)
        if digest == digest_ref:
            return dest
        else:
            warn("but checksum %s != %s, redownloading." % (digest, digest_ref))
            os.remove(fname)
    
    info("fetching %s into %s" % (url, savedir))
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    req = urlopen(url)
    with open(dest, 'wb') as f:
        f.write(req.read())
    digest = checksum_file(scheme, dest)
    if digest != digest_ref:
        fatal("%s %s mismatch:\nExpected: %s\nActual  : %s" % (
            dest, scheme, digest_ref, digest))
    return dest

#-----------------------------------------------------------------------------
# libzmq
#-----------------------------------------------------------------------------

def fetch_libzmq(savedir):
    """download and extract libzmq"""
    dest = pjoin(savedir, 'zeromq')
    if os.path.exists(dest):
        info("already have %s" % dest)
        return
    path = fetch_archive(savedir, libzmq_url, fname=libzmq, checksum=libzmq_checksum)
    tf = tarfile.open(path)
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
            elif sys.platform.startswith('linux-armv'):
                platform_dir = pjoin(HERE, 'include_linux-armv')
            else:
                platform_dir = pjoin(HERE, 'include_linux')
        else:
            return
    
    info("staging platform.hpp from: %s" % platform_dir)
    shutil.copy(pjoin(platform_dir, 'platform.hpp'), platform_hpp)


def copy_and_patch_libzmq(ZMQ, libzmq):
    """copy libzmq into source dir, and patch it if necessary.
    
    This command is necessary prior to running a bdist on Linux or OS X.
    """
    if sys.platform.startswith('win'):
        return
    # copy libzmq into zmq for bdist
    local = localpath('zmq',libzmq)
    if not ZMQ and not os.path.exists(local):
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
        # chmod u+w on the lib,
        # which can be user-read-only for some reason
        mode = os.stat(local).st_mode
        os.chmod(local, mode | stat.S_IWUSR)
        # patch install_name on darwin, instead of using rpath
        cmd = ['install_name_tool', '-id', '@loader_path/../%s'%libzmq, local]
        try:
            p = Popen(cmd, stdout=PIPE,stderr=PIPE)
        except OSError:
            fatal("install_name_tool not found, cannot patch libzmq for bundling.")
        out,err = p.communicate()
        if p.returncode:
            fatal("Could not patch bundled libzmq install_name: %s"%err, p.returncode)
        
