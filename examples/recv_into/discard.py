"""
use recv_into with an empty buffer to discard unwanted message frames

avoids unnecessary allocations for message frames that won't be used
"""

import logging
import os
import random
import secrets
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

import zmq

EMPTY = bytearray()


def subscriber(url: str) -> None:
    log = logging.getLogger("subscriber")
    with zmq.Context() as ctx, ctx.socket(zmq.SUB) as sub:
        sub.linger = 0
        sub.connect(url)
        sub.subscribe(b"")
        log.info("Receiving...")
        while True:
            frame_0 = sub.recv_string()
            if frame_0 == "exit":
                log.info("Exiting...")
                break
            elif frame_0 == "large":
                discarded_bytes = 0
                discarded_frames = 0
                while sub.rcvmore:
                    discarded_bytes += sub.recv_into(EMPTY)
                    discarded_frames += 1
                log.info(
                    "Discarding large message frames: %s, bytes: %s",
                    discarded_frames,
                    discarded_bytes,
                )
            else:
                msg: list = [frame_0]
                if sub.rcvmore:
                    msg.extend(sub.recv_multipart(flags=zmq.DONTWAIT))
                log.info("Received %s", msg)
    log.info("Done")


def publisher(url) -> None:
    log = logging.getLogger("publisher")
    choices = ["large", "small"]
    with zmq.Context() as ctx, ctx.socket(zmq.PUB) as pub:
        pub.linger = 1000
        pub.bind(url)
        time.sleep(1)
        for i in range(10):
            kind = random.choice(choices)
            frames = [kind.encode()]
            if kind == "large":
                for _ in range(random.randint(0, 5)):
                    chunk_size = random.randint(1024, 2048)
                    chunk = os.urandom(chunk_size)
                    frames.append(chunk)
            else:
                for _ in range(random.randint(0, 3)):
                    chunk_size = random.randint(0, 5)
                    chunk = secrets.token_hex(chunk_size).encode()
                    frames.append(chunk)
            nbytes = sum(len(chunk) for chunk in frames)
            log.info("Sending %s: %s bytes", kind, nbytes)
            pub.send_multipart(frames)
            time.sleep(0.1)
        log.info("Sending exit")
        pub.send(b"exit")
    log.info("Done")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    with TemporaryDirectory() as td:
        sock_path = Path(td) / "example.sock"
        url = f"ipc://{sock_path}"
        s_thread = Thread(
            target=subscriber, args=(url,), daemon=True, name="subscriber"
        )
        s_thread.start()
        publisher(url)
        s_thread.join(timeout=3)


if __name__ == "__main__":
    main()
