"""
ROUTER-ROUTER communication example

ideal for P2P applications that need a socket that is able to connect
to several other peers simultaneously, while also being able
to receive messages

In this example, aiowire.EventLoop is used to await all tasks launched
within it, while timing out after (here) 1 second.
This guarantees completion of tasks - even if they are infinite loops
- as long as they regularly call await.

Contributed by github:jcpinto54 and github:frobnitzem
"""

# Copyright (c) 2022 PyZMQ Developers.
# This example is in the public domain (CC-0)

import asyncio

from aiowire import EventLoop

import zmq
from zmq.asyncio import Context


class Server:
    def __init__(self, url: str):
        context = Context.instance()
        socket = context.socket(zmq.ROUTER)
        socket.setsockopt_string(zmq.IDENTITY, 'server')
        socket.bind(url)
        self.socket = socket

    async def run(self, ev: EventLoop):
        # `Wire` type receives the event loop as its single argument

        req = await self.socket.recv_multipart()
        print(f"Server received {req}")
        # identity of receptionist, empty frame, message content
        await self.socket.send_multipart([req[0], b'', b'whatup'])

        # continue to run by returning this `Wire`
        return self.run


class Client:
    def __init__(self, url: str, name: str):
        self.name = name

        context = Context.instance()
        socket = context.socket(zmq.ROUTER)
        socket.setsockopt_string(zmq.IDENTITY, name)
        socket.connect(url)
        self.socket = socket

    async def run(self, ev: EventLoop):
        await asyncio.sleep(0.1)
        # identity of receptionist, empty frame, message content
        await self.socket.send_multipart([b'server', b'', b'cheers'])
        rep = await self.socket.recv_multipart()
        print(f"{self.name} received {rep}")

        # continue to run by returning this `Wire`
        return self.run


async def main() -> None:
    url = 'inproc://test_zmq'
    srv = Server(url)
    romeo = Client(url, 'romeo')
    sierra = Client(url, 'sierra')

    async with EventLoop(1.0) as ev:
        ev.start(romeo.run)
        ev.start(sierra.run)
        ev.start(srv.run)


if __name__ == "__main__":
    asyncio.run(main())
