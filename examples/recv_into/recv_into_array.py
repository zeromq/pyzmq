"""
Use recv_into to receive data directly into a numpy array
"""

import numpy as np
import numpy.testing as nt

import zmq

url = "inproc://test"


def main() -> None:
    A = (np.random.random((5, 5)) * 255).astype(dtype=np.int64)
    B = np.empty_like(A)
    assert not (A == B).all()

    with (
        zmq.Context() as ctx,
        ctx.socket(zmq.PUSH) as push,
        ctx.socket(zmq.PULL) as pull,
    ):
        push.bind(url)
        pull.connect(url)
        print("sending:\n", A)
        push.send(A)
        bytes_received = pull.recv_into(B)
        print(f"received {bytes_received} bytes:\n", B)
        assert bytes_received == A.nbytes
        nt.assert_allclose(A, B)


if __name__ == "__main__":
    main()
