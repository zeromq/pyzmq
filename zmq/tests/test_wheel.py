"""Light tests to verify that the wheel works

Just import things
"""

import os
import sys

import pytest


@pytest.mark.wheel
def test_wheel():
    import zmq

    ctx = zmq.Context()
    s = ctx.socket(zmq.PUSH)
    s.close()
    ctx.term()


@pytest.mark.skipif(sys.platform != "win32", reason="only on Windows")
@pytest.mark.wheel
def test_bundle_msvcp():
    import zmq

    zmq_dir = os.path.abspath(os.path.dirname(zmq.__file__))
    # pyzmq.libs is *next to* zmq itself
    pyzmq_lib_dir = os.path.join(zmq_dir, os.pardir, "pyzmq.libs")
    dlls = sorted([name for name in os.listdir(pyzmq_lib_dir) if name.endswith(".dll")])
    print(dlls)
    assert "vcruntime140.dll" not in dlls
    for expected in ["concrt140.dll", "msvcp140.dll"]:
        assert expected in dlls

    assert any(dll.startswith("libzmq") for dll in dlls)
    assert any(dll.startswith("libsodium") for dll in dlls)
