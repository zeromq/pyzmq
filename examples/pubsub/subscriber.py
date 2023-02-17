"""A test that subscribes to NumPy arrays.

Uses REQ/REP (on PUB/SUB socket + 1) to synchronize
"""

# -----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file LICENSE.BSD, distributed as part of this software.
# -----------------------------------------------------------------------------


import sys
import time

import zmq


def sync(connect_to: str) -> None:
    # use connect socket + 1
    sync_with = ':'.join(
        connect_to.split(':')[:-1] + [str(int(connect_to.split(':')[-1]) + 1)]
    )
    ctx = zmq.Context.instance()
    s = ctx.socket(zmq.REQ)
    s.connect(sync_with)
    s.send(b'READY')
    s.recv()


def main() -> None:
    if len(sys.argv) != 3:
        print('usage: subscriber <connect_to> <array-count>')
        sys.exit(1)

    try:
        connect_to = sys.argv[1]
        array_count = int(sys.argv[2])
    except (ValueError, OverflowError) as e:
        print('array-count must be integers')
        sys.exit(1)

    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.connect(connect_to)
    s.setsockopt(zmq.SUBSCRIBE, b'')

    sync(connect_to)

    start = time.process_time()

    print("Receiving arrays...")
    for i in range(array_count):
        a = s.recv_pyobj()
    print("   Done.")

    end = time.process_time()

    elapsed = end - start

    throughput = float(array_count) / elapsed

    message_size = a.nbytes
    megabits = float(throughput * message_size * 8) / 1000000

    print(f"message size: {message_size:.0f} [B]")
    print(f"array count: {array_count:.0f}")
    print(f"mean throughput: {throughput:.0f} [msg/s]")
    print(f"mean throughput: {megabits:.3f} [Mb/s]")

    time.sleep(1.0)


if __name__ == "__main__":
    main()
