"""A test that publishes NumPy arrays.

Uses XPUB to wait for subscription to start
"""

# -----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file LICENSE.BSD, distributed as part of this software.
# -----------------------------------------------------------------------------

from argparse import ArgumentParser

import numpy

import zmq


def send_array(
    socket: zmq.Socket, array: numpy.ndarray, flags=0, copy=True, track=False
):
    md = {
        "shape": array.shape,
        # is there a better way to serialize dtypes?
        "dtype": str(array.dtype),
    }
    socket.send_json(md, flags | zmq.SNDMORE)
    return socket.send(array, flags, copy=copy, track=track)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--url", default="tcp://127.0.0.1:5555")
    parser.add_argument(
        "-n", "--count", default=10, type=int, help="number of arrays to send"
    )
    parser.add_argument(
        "--size",
        default=1024,
        type=int,
        help="size of the arrays to send (length of each dimension). Total size is size**nd",
    )
    parser.add_argument("--nd", default=2, type=int, help="number of dimensions")
    args = parser.parse_args()
    bind_to = args.url
    ctx = zmq.Context()
    s = ctx.socket(zmq.XPUB)
    s.bind(bind_to)
    print("Waiting for subscriber")
    s.recv()
    print("Sending arrays...")
    shape = (args.size,) * args.nd
    for i in range(args.count):
        a = numpy.random.random(shape)
        send_array(s, a)
    s.send_json({"done": True})
    print("   Done.")


if __name__ == "__main__":
    main()
