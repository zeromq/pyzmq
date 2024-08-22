"""Light tests to verify that the wheel works

Just import things
"""

import os
import platform
import sys
from fnmatch import fnmatch

import pytest

try:
    from importlib.metadata import distribution
except ImportError:
    from importlib_metadata import distribution


@pytest.mark.parametrize("feature", ["curve", "ipc"])
def test_has(feature):
    import zmq

    if feature == 'ipc' and sys.platform.startswith('win32'):
        # IPC support is broken in enough cases on Windows
        # that we can't ship wheels with it (for now)
        assert not zmq.has(feature)
    else:
        assert zmq.has(feature)


def test_simple_socket():
    import zmq

    ctx = zmq.Context()
    s = ctx.socket(zmq.PUSH)
    s.close()
    ctx.term()


@pytest.mark.skipif(
    sys.platform != "win32" or platform.python_implementation() != "CPython",
    reason="only on CPython + Windows",
)
def test_bundle_msvcp():
    import zmq

    zmq_dir = os.path.abspath(os.path.dirname(zmq.__file__))
    # pyzmq.libs is *next to* zmq itself
    pyzmq_lib_dir = os.path.join(zmq_dir, os.pardir, "pyzmq.libs")
    dlls = []
    if os.path.exists(pyzmq_lib_dir):
        dlls = sorted(
            name for name in os.listdir(pyzmq_lib_dir) if name.endswith(".dll")
        )
    print(dlls)
    # Is concrt140 needed? delvewheel doesn't detect it anymore
    # check for vcruntime?
    should_bundle = []
    shouldnt_bundle = ["msvcp140*.dll"]

    for pattern in shouldnt_bundle:
        matched = [dll for dll in dlls if fnmatch(dll, pattern)]
        assert not matched

    for pattern in should_bundle:
        matched = [dll for dll in dlls if fnmatch(dll, pattern)]
        assert matched


@pytest.mark.parametrize(
    "license_name",
    [
        "LICENSE.md",
        "LICENSE.zeromq.txt",
        "LICENSE.libsodium.txt",
    ],
)
def test_license_files(license_name):
    pyzmq = distribution("pyzmq")
    license_files = [f for f in pyzmq.files if "licenses" in str(f)]
    license_file_names = [f.name for f in license_files]
    assert license_name in license_file_names
    for license_file in license_files:
        if license_file.name == license_name:
            break
    assert license_file.locate().exists()
