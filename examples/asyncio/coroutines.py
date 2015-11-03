"""Example using zmq with asyncio coroutines"""
# Copyright (c) PyZMQ Developers.
# This example is in the public domain (CC-0)

import time

import zmq
from zmq.asyncio import Context, Poller, ZMQEventLoop
import asyncio

url = 'tcp://127.0.0.1:5555'

loop = ZMQEventLoop()
asyncio.set_event_loop(loop)

ctx = Context()

@asyncio.coroutine
def ping():
    """print dots to indicate idleness"""
    while True:
        yield from asyncio.sleep(0.5)
        print('.')

@asyncio.coroutine
def receiver():
    """receive messages with polling"""
    pull = ctx.socket(zmq.PULL)
    pull.connect(url)
    poller = Poller()
    poller.register(pull, zmq.POLLIN)
    while True:
        events = yield from poller.poll()
        if pull in dict(events):
            print("recving", events)
            msg = yield from pull.recv_multipart()
            print('recvd', msg)

@asyncio.coroutine
def sender():
    """send a message every second"""
    tic = time.time()
    push = ctx.socket(zmq.PUSH)
    push.bind(url)
    while True:
        print("sending")
        yield from push.send_multipart([str(time.time() - tic).encode('ascii')])
        yield from asyncio.sleep(1)

loop.run_until_complete(asyncio.wait([
    ping(),
    receiver(),
    sender(),
]))
