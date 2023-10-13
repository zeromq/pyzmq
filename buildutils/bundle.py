"""utilities for fetching build dependencies."""

# -----------------------------------------------------------------------------
#  Copyright (C) PyZMQ Developers
#  Distributed under the terms of the Modified BSD License.
#
#  This bundling code is largely adapted from pyzmq-static's get.sh by
#  Brandon Craig-Rhodes, which is itself BSD licensed.
# -----------------------------------------------------------------------------


import hashlib
import os
import shutil
import sys
import zipfile
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory
from unittest import mock
from urllib.request import urlopen

from .msg import fatal, info, warn

pjoin = os.path.join

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

bundled_version = (4, 3, 5)
vs = '%i.%i.%i' % bundled_version
x, y, z = bundled_version
libzmq = "zeromq-%s.zip" % vs
download_url = f"https://github.com/zeromq/libzmq/releases/download/v{vs}"

libzmq_url = f"{download_url}/{libzmq}"
libzmq_checksum = "sha1:a8a8b800cbb3e13db0246473362d4d1f17813879"


HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------


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
    if checksum:
        scheme, digest_ref = checksum.split(':')
    else:
        scheme = "sha256"
        digest_ref = None

    if os.path.exists(dest) and not force:
        info("already have %s" % dest)
        digest = checksum_file(scheme, fname)
        if digest == digest_ref or not digest_ref:
            return dest
        else:
            warn(f"but checksum {digest} != {digest_ref}, redownloading.")
            os.remove(fname)

    info(f"fetching {url} into {savedir}")
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    req = urlopen(url)
    with open(dest, 'wb') as f:
        f.write(req.read())
    digest = checksum_file(scheme, dest)
    if digest_ref and digest != digest_ref:
        fatal(
            "%s %s mismatch:\nExpected: %s\nActual  : %s"
            % (dest, scheme, digest_ref, digest)
        )
    elif not digest_ref:
        warn(f"No digest to check, got: {scheme}:{digest}")
    return dest


# -----------------------------------------------------------------------------
# libzmq
# -----------------------------------------------------------------------------


def fetch_and_extract(savedir, extract_to, url, fname, checksum):
    """Download and extract an archive"""
    dest = pjoin(savedir, extract_to)
    if os.path.exists(dest):
        info("already have %s" % dest)
        return
    archive = fetch_archive(savedir, url, fname=fname, checksum=checksum)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(savedir)
        with_version = pjoin(savedir, zf.namelist()[0])
    # remove version suffix:
    shutil.move(with_version, dest)
    # remove archive when we are done
    os.remove(archive)


def fetch_libzmq(savedir):
    """download and extract libzmq"""
    fetch_and_extract(
        savedir, 'zeromq', url=libzmq_url, fname=libzmq, checksum=libzmq_checksum
    )


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
        platform_dir = pjoin(HERE, 'include_win32')
    else:
        info("attempting ./configure to generate platform.hpp")
        failed = False
        try:
            p = Popen(
                ["./configure", "--disable-drafts"],
                cwd=zmqroot,
                stdout=PIPE,
                stderr=PIPE,
            )
        except OSError as err:
            failed = True
            e = str(err)
        else:
            o, e = p.communicate()
            e = e.decode("utf8", "replace")
            failed = bool(p.returncode)
        if failed:
            warn("failed to configure libzmq:\n%s" % e)
            if sys.platform == 'darwin':
                platform_dir = pjoin(HERE, 'include_darwin')
            elif sys.platform.startswith('freebsd'):
                platform_dir = pjoin(HERE, 'include_freebsd')
            elif sys.platform.startswith('linux-armv'):
                platform_dir = pjoin(HERE, 'include_linux-armv')
            elif sys.platform.startswith('sunos'):
                platform_dir = pjoin(HERE, 'include_sunos')
            else:
                # check for musl (alpine)
                from packaging import tags

                if any('musllinux' in tag.platform for tag in tags.sys_tags()):
                    info("Detected musllinux (likely alpine)")
                    platform_dir = pjoin(HERE, 'include_linux-musl')
                else:
                    platform_dir = pjoin(HERE, 'include_linux')
        else:
            return

    info("staging platform.hpp from: %s" % platform_dir)
    shutil.copy(pjoin(platform_dir, 'platform.hpp'), platform_hpp)


def check_checksums():
    """Check all the checksums!"""
    _failed = False

    def less_fatal(msg):
        """Mock fatal log message to set failed flag instead of exiting

        So we can see multiple failures in one run,
        e.g. when updating the bundled libzmq version.
        """
        warn(msg)
        nonlocal _failed
        _failed = True

    with TemporaryDirectory() as savedir, mock.patch.dict(globals(), fatal=less_fatal):
        fetch_archive(
            savedir,
            libzmq_url,
            fname=libzmq,
            checksum=libzmq_checksum,
        )
    if not _failed:
        print("All ok!")
    return _failed


if __name__ == "__main__":
    # allow python -m buildutils.bundle to get bundled version
    if len(sys.argv) > 1 and sys.argv[1] == "checksums":
        sys.exit(check_checksums())
    else:
        print(vs)
