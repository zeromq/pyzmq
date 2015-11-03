"""Example using zmq with tornado coroutines"""
# Copyright (c) PyZMQ Developers.
# This example is in the public domain (CC-0)

import time

import zmq
from zmq.eventloop.future import Context, Poller
from zmq.eventloop.ioloop import IOLoop

from tornado import gen

url = 'tcp://127.0.0.1:5555'

ctx = Context()

@gen.coroutine
def ping():
    """print dots to indicate idleness"""
    while True:
        yield gen.sleep(0.25)
        print('.')

@gen.coroutine
def receiver():
    """receive messages with poll and timeout"""
    pull = ctx.socket(zmq.PULL)
    pull.connect(url)
    poller = Poller()
    poller.register(pull, zmq.POLLIN)
    while True:
        events = yield poller.poll(timeout=500)
        if pull in dict(events):
            print("recving", events)
            msg = yield pull.recv_multipart()
            print('recvd', msg)
        else:
            print("nothing to recv")

@gen.coroutine
def sender():
    """send a message every second"""
    tic = time.time()
    push = ctx.socket(zmq.PUSH)
    push.bind(url)
    poller = Poller()
    poller.register(push, zmq.POLLOUT)
    while True:
        print("sending")
        yield push.send_multipart([str(time.time() - tic).encode('ascii')])
        yield gen.sleep(1)

loop = IOLoop.instance()

loop.add_callback(ping)
loop.add_callback(receiver)
loop.add_callback(sender)
loop.start()

