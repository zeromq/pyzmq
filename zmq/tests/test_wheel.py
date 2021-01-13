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
    dlls = sorted([name for name in os.listdir(zmq_dir) if name.endswith(".dll")])
    assert dlls == ["concrt140.dll", "msvcp140.dll"]
