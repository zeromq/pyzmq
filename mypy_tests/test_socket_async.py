from __future__ import annotations

import asyncio

import zmq
import zmq.asyncio


async def main() -> None:
    ctx = zmq.asyncio.Context()

    # shadow exercise
    sync_ctx: zmq.Context = zmq.Context.shadow(ctx)
    ctx2: zmq.asyncio.Context = zmq.asyncio.Context.shadow(sync_ctx)
    ctx2 = zmq.asyncio.Context(sync_ctx)

    url = "tcp://127.0.0.1:5555"
    pub = ctx.socket(zmq.PUB)
    sub = ctx.socket(zmq.SUB)
    pub.bind(url)
    sub.connect(url)
    sub.subscribe(b"")
    await asyncio.sleep(1)

    # shadow exercise
    sync_sock: zmq.Socket[bytes] = zmq.Socket.shadow(pub)
    s2: zmq.asyncio.Socket = zmq.asyncio.Socket(sync_sock)
    s2 = zmq.asyncio.Socket.from_socket(sync_sock)

    print("sending")
    await pub.send(b"plain")
    await pub.send(b"plain")
    await pub.send_multipart([b"topic", b"Message"])
    await pub.send_multipart([b"topic", b"Message"])
    await pub.send_string("asdf")
    await pub.send_pyobj(123)
    await pub.send_json({"a": "5"})

    print("receiving")
    msg_bytes: bytes = await sub.recv()
    msg_frame: zmq.Frame = await sub.recv(copy=False)
    msg_list: list[bytes] = await sub.recv_multipart()
    msg_frames: list[zmq.Frame] = await sub.recv_multipart(copy=False)
    s: str = await sub.recv_string()
    obj = await sub.recv_pyobj()
    d = await sub.recv_json()

    pub.close()
    sub.close()


if __name__ == "__main__":
    asyncio.run(main())
