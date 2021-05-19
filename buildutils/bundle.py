"""utilities for fetching build dependencies."""

# -----------------------------------------------------------------------------
#  Copyright (C) PyZMQ Developers
#  Distributed under the terms of the Modified BSD License.
#
#  This bundling code is largely adapted from pyzmq-static's get.sh by
#  Brandon Craig-Rhodes, which is itself BSD licensed.
# -----------------------------------------------------------------------------


import os
import shutil
import sys
import tarfile
import hashlib
import platform
import zipfile
from subprocess import Popen, PIPE
from tempfile import TemporaryDirectory
from unittest import mock
from urllib.request import urlopen

from .msg import fatal, info, warn

pjoin = os.path.join

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

bundled_version = (4, 3, 4)
vs = '%i.%i.%i' % bundled_version
x, y, z = bundled_version
libzmq = "zeromq-%s.tar.gz" % vs
download_url = f"https://github.com/zeromq/libzmq/releases/download/v{vs}"

libzmq_url = f"{download_url}/{libzmq}"
libzmq_checksum = (
    "sha256:c593001a89f5a85dd2ddf564805deb860e02471171b3f204944857336295c3e5"
)

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)

vcversion = 141

if platform.architecture()[0] == '64bit':
    msarch = '-x64'
else:
    msarch = ''

libzmq_dll = f"libzmq-v{vcversion}{msarch}-{x}_{y}_{z}.zip"
libzmq_dll_url = f"{download_url}/{libzmq_dll}"

libzmq_dll_checksums = {
    "libzmq-v140-4_3_4.zip": "sha256:05b7c42fe8d5feb2795d32f71f7d900083530ee6fdd15575bfc8d1b3fb8643f7",
    "libzmq-v140-x64-4_3_4.zip": "sha256:d5d75bd502d7935af3cf80734f81069be78420331c54814d0aab6d64adf450ae",
    "libzmq-v141-4_3_4.zip": "sha256:acfc997f036018b8dc8ab5b3a1d1444bba6ba5621e91c756d07cd9447db19672",
    "libzmq-v141-x64-4_3_4.zip": "sha256:4bb29d6fed20bd175a82317676c7e940356cd358b624efae8569c7ee11c45636",
}

libzmq_dll_checksum = libzmq_dll_checksums.get(libzmq_dll)

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
            warn("but checksum %s != %s, redownloading." % (digest, digest_ref))
            os.remove(fname)

    info("fetching %s into %s" % (url, savedir))
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
            else:
                platform_dir = pjoin(HERE, 'include_linux')
        else:
            return

    info("staging platform.hpp from: %s" % platform_dir)
    shutil.copy(pjoin(platform_dir, 'platform.hpp'), platform_hpp)


def fetch_libzmq_dll(savedir):
    """Download binary release of libzmq for windows

    vcversion specifies the MSVC runtime version to use
    """

    dest = pjoin(savedir, 'zmq.h')
    if os.path.exists(dest):
        info("already have %s" % dest)
        return
    path = fetch_archive(
        savedir, libzmq_dll_url, fname=libzmq_dll, checksum=libzmq_dll_checksum
    )
    archive = zipfile.ZipFile(path)
    to_extract = []
    for name in archive.namelist():
        if not name.endswith(".exe"):
            to_extract.append(name)
    archive.extractall(savedir, members=to_extract)
    archive.close()


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
        for dll, checksum in libzmq_dll_checksums.items():
            fetch_archive(
                savedir,
                f"{download_url}/{dll}",
                fname=dll,
                checksum=checksum,
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
