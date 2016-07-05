import asyncio
from tornado.platform.asyncio import AsyncIOMainLoop
AsyncIOMainLoop().install()

# This must be instantiated after the installing the IOLoop
queue = asyncio.Queue()

async def pushing():
    while True:
        await queue.put("hello")
        await asyncio.sleep(1)

async def pulling():
    while True:
        greeting = await queue.get()
        print(greeting)

def zmq_tornado_loop():
    from zmq.eventloop.ioloop import IOLoop
    loop = IOLoop.current()
    loop.spawn_callback(pushing)
    loop.spawn_callback(pulling)
    loop.start()

if __name__ == '__main__':
    zmq_tornado_loop()

