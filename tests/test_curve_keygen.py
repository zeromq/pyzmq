import json
import sys
from subprocess import run

import pytest

import zmq
from zmq.utils import z85

pytestmark = pytest.mark.skipif(not zmq.has("curve"), reason="Requires CURVE")


curve_keygen = [sys.executable, "-m", "zmq.curve_keygen"]


def _curve_test(public: bytes, secret: bytes):
    with (
        zmq.Context() as ctx,
        ctx.socket(zmq.PUSH) as push,
        ctx.socket(zmq.PULL) as pull,
    ):
        push.curve_server = True
        push.curve_secretkey = secret
        push.curve_publickey = public
        pull.curve_serverkey = public
        pull.curve_publickey, pull.curve_secretkey = zmq.curve_keypair()
        push.linger = pull.linger = 0
        push.sndtimeo = 3_000
        pull.rcvtimeo = 3_000
        # url = "inproc://test"
        push.bind_to_random_port("tcp://127.0.0.1")
        pull.connect(push.last_endpoint)
        push.send(b"hi")
        assert pull.recv() == b"hi"


def test_curve_keygen_help():
    p = run(curve_keygen + ["-h"], capture_output=True, text=True, check=True)
    assert "python3 -m zmq.curve_keygen" in p.stdout
    assert "--json" in p.stdout


def test_curve_keygen():
    p = run(curve_keygen, capture_output=True, text=True, check=True)
    lines = p.stdout.splitlines()
    assert "== CURVE PUBLIC KEY ==" in lines
    public = lines[lines.index("== CURVE PUBLIC KEY ==") + 1]
    assert z85.decode(public)
    assert "== CURVE SECRET KEY ==" in lines
    secret = lines[lines.index("== CURVE SECRET KEY ==") + 1]
    assert z85.decode(secret)
    assert p.stdout.endswith("\n")
    _curve_test(public.encode(), secret.encode())


def test_curve_keygen_json():
    p = run(curve_keygen + ["--json"], capture_output=True, text=True, check=True)
    out = json.loads(p.stdout)
    assert z85.decode(out["public"])
    assert z85.decode(out["secret"])
    assert p.stdout.endswith("\n")
    _curve_test(out["public"].encode(), out["secret"].encode())


def test_curve_keygen_secret():
    public, secret = zmq.curve_keypair()
    p = run(
        curve_keygen + ["--secret", secret, "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(p.stdout)
    assert z85.decode(out["public"])
    assert out["public"].encode() == public
