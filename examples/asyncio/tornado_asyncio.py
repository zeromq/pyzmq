"""Example showing ZMQ with asyncio and tornadoweb integration."""

# Copyright (c) PyZMQ Developers.
# This example is in the public domain (CC-0)

import asyncio

from tornado.ioloop import IOLoop

import zmq.asyncio


async def pushing() -> None:
    server = zmq.asyncio.Context.instance().socket(zmq.PUSH)
    server.bind('tcp://*:9000')
    while True:
        await server.send(b"Hello")
        await asyncio.sleep(1)


async def pulling() -> None:
    client = zmq.asyncio.Context.instance().socket(zmq.PULL)
    client.connect('tcp://127.0.0.1:9000')
    while True:
        greeting = await client.recv()
        print(greeting)


def main() -> None:
    loop = IOLoop.current()
    loop.spawn_callback(pushing)
    loop.spawn_callback(pulling)
    loop.start()


if __name__ == '__main__':
    main()
