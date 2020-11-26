"""
Test our typing with mypy
"""
import glob
import os
import sys
import zmq
from subprocess import Popen, PIPE, STDOUT

import pytest

pytest.importorskip("mypy")

zmq_dir = os.path.dirname(zmq.__file__)


def resolve_repo_dir(path):
    """Resolve a dir in the repo

    Resolved relative to zmq dir

    fallback on CWD (e.g. test run from repo, zmq installed, not -e)
    """
    resolved_path = os.path.join(os.path.dirname(zmq_dir), path)

    # fallback on CWD
    if not os.path.exists(resolved_path):
        resolved_path = path
    return resolved_path


examples_dir = resolve_repo_dir("examples")
mypy_dir = resolve_repo_dir("mypy_tests")


def run_mypy(path):
    """Run mypy for a path

    Captures output and reports it on errors
    """
    p = Popen([sys.executable, "-m", "mypy", path], stdout=PIPE, stderr=STDOUT)
    o, _ = p.communicate()
    out = o.decode("utf8", "replace")
    print(out)
    assert p.returncode == 0, out


if os.path.exists(examples_dir):
    examples = [
        d
        for d in os.listdir(examples_dir)
        if os.path.isdir(os.path.join(examples_dir, d))
    ]


@pytest.mark.skipif(
    not os.path.exists(examples_dir), reason="only test from examples directory"
)
@pytest.mark.parametrize("example", examples)
def test_mypy_example(example):
    example_dir = os.path.join(examples_dir, example)
    run_mypy(example_dir)


if os.path.exists(mypy_dir):
    mypy_tests = [p for p in os.listdir(mypy_dir) if p.endswith(".py")]


@pytest.mark.parametrize("filename", mypy_tests)
def test_mypy(filename):
    run_mypy(os.path.join(mypy_dir, filename))
