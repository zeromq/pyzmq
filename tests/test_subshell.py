import sys

import pytest
from conftest import recv

import zmq

if sys.version_info < (3, 14):
    pytest.skip("Requires Python 3.14")

from concurrent.futures import InterpreterPoolExecutor


def echo(url):
    with zmq.Context() as ctx, ctx.socket(zmq.ROUTER) as s:
        s.bind(url)
        msg = s.recv_multipart()
        print(msg)


def test_subshell(context, socket):
    s = socket(zmq.DEALER)
    url = "tcp://127.0.0.1:5555"
    with InterpreterPoolExecutor(1) as pool:
        f = pool.submit(echo, url)
        try:
            f.result(timeout=1)
        except TimeoutError:
            pass
        else:
            pytest.fail("echo task exited prematurely...")
        s.connect(url)
        msg = b"msg"
        s.send(msg)
        recvd = recv(s)
        assert recvd == msg
