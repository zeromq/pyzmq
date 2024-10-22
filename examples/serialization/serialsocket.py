"""A Socket subclass that adds some serialization methods."""

import hmac
import pickle
import secrets
import zlib
from hashlib import sha256
from typing import Any, Dict, cast

import numpy

import zmq


class SerializingSocket(zmq.Socket):
    """A class with some extra serialization methods

    send_zipped_pickle is just like send_pyobj, but uses
    zlib to compress the stream before sending,
    and signs messages with a key for authentication because
    we must never load untrusted pickles.

    send_array sends numpy arrays without copying the array,
    along with metadata necessary
    for reconstructing the array on the other side (dtype,shape).
    """

    signing_key: bytes

    def sign(self, buffer: bytes) -> bytes:
        return hmac.HMAC(
            self.signing_key,
            buffer,
            sha256,
        ).digest()

    def send_zipped_pickle(
        self,
        obj: Any,
        flags: int = 0,
        *,
        protocol: int = pickle.HIGHEST_PROTOCOL,
    ) -> None:
        """pack and compress an object with pickle and zlib."""
        pobj = pickle.dumps(obj, protocol)
        zobj = zlib.compress(pobj)
        shrinkage = len(pobj) / len(zobj)
        print(f'zipped pickle is {len(zobj)} bytes ({shrinkage:.1f}x smaller)')
        signature = self.sign(zobj)
        self.send(signature, flags=flags | zmq.SNDMORE)
        return self.send(zobj, flags=flags)

    def recv_zipped_pickle(self, flags: int = 0) -> Any:
        """reconstruct a Python object sent with zipped_pickle"""
        recvd_signature = self.recv()
        assert self.rcvmore
        zobj = self.recv(flags)
        check_signature = self.sign(zobj)
        if not hmac.compare_digest(recvd_signature, check_signature):
            raise ValueError("Invalid signature")

        # check signature before loading with pickle
        # pickle.loads involves arbitrary code execution
        pobj = zlib.decompress(zobj)
        return pickle.loads(pobj)

    def send_array(
        self, A: numpy.ndarray, flags: int = 0, copy: bool = True, track: bool = False
    ) -> Any:
        """send a numpy array with metadata"""
        md = dict(
            dtype=str(A.dtype),
            shape=A.shape,
        )
        self.send_json(md, flags | zmq.SNDMORE)
        return self.send(A, flags, copy=copy, track=track)

    def recv_array(
        self, flags: int = 0, copy: bool = True, track: bool = False
    ) -> numpy.ndarray:
        """recv a numpy array"""
        md = cast(Dict[str, Any], self.recv_json(flags=flags))
        msg = self.recv(flags=flags, copy=copy, track=track)
        A = numpy.frombuffer(msg, dtype=md['dtype'])  # type: ignore
        return A.reshape(md['shape'])


class SerializingContext(zmq.Context[SerializingSocket]):
    _socket_class = SerializingSocket


def main() -> None:
    ctx = SerializingContext()
    push = ctx.socket(zmq.PUSH)
    pull = ctx.socket(zmq.PULL)

    push.bind('inproc://a')
    pull.connect('inproc://a')
    # 'distribute' shared secret
    push.signing_key = pull.signing_key = secrets.token_bytes(32)
    # all ones is a best-case scenario for zip
    A = numpy.ones((1024, 1024))
    print(f"Array is {A.nbytes} bytes")

    # send/recv with pickle+zip
    push.send_zipped_pickle(A)
    B = pull.recv_zipped_pickle()
    # now try non-copying version
    push.send_array(A, copy=False)
    C = pull.recv_array(copy=False)
    print("Checking zipped pickle...")
    print("Okay" if (A == B).all() else "Failed")
    print("Checking send_array...")
    print("Okay" if (C == B).all() else "Failed")

    print("Checking incorrect signature...")
    push.signing_key = b"wrong"
    push.send_zipped_pickle(A)
    try:
        B = pull.recv_zipped_pickle()
    except ValueError:
        print("Okay")
    else:
        print("Failed")


if __name__ == '__main__':
    main()
