"""Light tests to verify that the wheel works

Just import things
"""

import os
import platform
import sys
from fnmatch import fnmatch

import pytest


@pytest.mark.parametrize("feature", ["curve", "ipc"])
def test_has(feature):
    import zmq

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
    should_bundle = ["msvcp140*.dll"]
    shouldnt_bundle = []

    for pattern in shouldnt_bundle:
        matched = [dll for dll in dlls if fnmatch(dll, pattern)]
        assert not matched

    for pattern in should_bundle:
        matched = [dll for dll in dlls if fnmatch(dll, pattern)]
        assert matched
