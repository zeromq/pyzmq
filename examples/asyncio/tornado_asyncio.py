import asyncio
import zmq.asyncio
from tornado.platform.asyncio import AsyncIOMainLoop
AsyncIOMainLoop().install()

# This must be instantiated after the installing the IOLoop
queue = asyncio.Queue()
ctx = zmq.asyncio.Context()

async def pushing():
    server = ctx.socket(zmq.PUSH)
    server.bind('tcp://*:9000')
    while True:
        await server.send(b"Hello")

async def pulling():
    client = ctx.socket(zmq.PULL)
    client.connect('tcp://127.0.0.1:9000')
    while True:
        greeting = await client.recv()
        print(greeting)

def zmq_tornado_loop():
    from zmq.eventloop.ioloop import IOLoop
    loop = IOLoop.current()
    loop.spawn_callback(pushing)
    loop.spawn_callback(pulling)
    loop.start()

if __name__ == '__main__':
    zmq_tornado_loop()

