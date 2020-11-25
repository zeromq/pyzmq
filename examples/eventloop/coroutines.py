"""Example using zmq with tornado coroutines"""
# Copyright (c) PyZMQ Developers.
# This example is in the public domain (CC-0)

import time

import zmq
from zmq.eventloop.future import Context, Poller
from tornado.ioloop import IOLoop

from tornado import gen

url = 'tcp://127.0.0.1:5555'

ctx = Context.instance()


async def ping():
    """print dots to indicate idleness"""
    while True:
        await gen.sleep(0.25)
        print('.')


async def receiver():
    """receive messages with poll and timeout"""
    pull = ctx.socket(zmq.PULL)
    pull.connect(url)
    poller = Poller()
    poller.register(pull, zmq.POLLIN)
    while True:
        events = await poller.poll(timeout=500)
        if pull in dict(events):
            print("recving", events)
            msg = await pull.recv_multipart()
            print('recvd', msg)
        else:
            print("nothing to recv")


async def sender():
    """send a message every second"""
    tic = time.time()
    push = ctx.socket(zmq.PUSH)
    push.bind(url)
    poller = Poller()
    poller.register(push, zmq.POLLOUT)
    while True:
        print("sending")
        await push.send_multipart([str(time.time() - tic).encode("ascii")])
        await gen.sleep(1)


loop = IOLoop.instance()

loop.spawn_callback(ping)
loop.spawn_callback(receiver)
loop.spawn_callback(sender)
loop.start()
