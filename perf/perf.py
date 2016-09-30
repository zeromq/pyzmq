#!/usr/bin/env python
# coding: utf-8

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.
#
#  Some original test code Copyright (c) 2007-2010 iMatix Corporation,
#  Used under LGPLv3

import argparse
from multiprocessing import Process
import time

try:
    now = time.monotonic
except AttributeError:
    now = time.time

import zmq

def parse_args(argv=None):

    parser = argparse.ArgumentParser(description='Run a zmq performance test')
    parser.add_argument('-p', '--poll', action='store_true',
                       help='use a zmq Poller instead of raw send/recv')
    parser.add_argument('-c', '--copy', action='store_true',
                       help='copy messages instead of using zero-copy')
    parser.add_argument('-s', '--size', type=int, default=10240,
                       help='size (in bytes) of the test message')
    parser.add_argument('-n', '--count', type=int, default=10240,
                       help='number of test messages to send')
    parser.add_argument('--url', dest='url', type=str, default='tcp://127.0.0.1:5555',
                       help='the zmq URL on which to run the test')
    parser.add_argument(dest='test', type=str, default='lat', choices=['lat', 'thr'],
                       help='which test to run')
    return parser.parse_args(argv)

def latency_echo(url, count, poll, copy):
    """echo messages on a REP socket
    
    Should be started before `latency`
    """
    ctx = zmq.Context()
    s = ctx.socket(zmq.REP)

    if poll:
        p = zmq.Poller()
        p.register(s)

    s.bind(url)
    
    block = zmq.NOBLOCK if poll else 0
    
    for i in range(count):
        if poll:
            res = p.poll()
        msg = s.recv(block, copy=copy)

        if poll:
            res = p.poll()
        s.send(msg, block, copy=copy)
    
    msg = s.recv()
    assert msg == b'done'
    
    s.close()
    ctx.term()
    
def latency(url, count, size, poll, copy):
    """Perform a latency test"""
    ctx = zmq.Context()
    s = ctx.socket(zmq.REQ)
    s.setsockopt(zmq.LINGER, -1)
    s.connect(url)
    if poll:
        p = zmq.Poller()
        p.register(s)

    msg = b' ' * size

    block = zmq.NOBLOCK if poll else 0
    time.sleep(1)
    start = now()

    for i in range (0, count):
        if poll:
            res = p.poll()
            assert(res[0][1] & zmq.POLLOUT)
        s.send(msg, block, copy=copy)

        if poll:
            res = p.poll()
            assert(res[0][1] & zmq.POLLIN)
        msg = s.recv(block, copy=copy)
        
        assert len(msg) == size

    elapsed = now() - start

    s.send(b'done')

    latency = 1e6 * elapsed / (count * 2.)

    print ("message size   : %8i     [B]" % (size, ))
    print ("roundtrip count: %8i     [msgs]" % (count, ))
    print ("mean latency   : %12.3f [µs]" % (latency, ))
    print ("test time      : %12.3f [s]" % (elapsed, ))

def pusher(url, count, size, poll, copy):
    """send a bunch of messages on a PUSH socket"""
    ctx = zmq.Context()
    s = ctx.socket(zmq.PUSH)

    #  Add your socket options here.
    #  For example ZMQ_RATE, ZMQ_RECOVERY_IVL and ZMQ_MCAST_LOOP for PGM.

    if poll:
        p = zmq.Poller()
        p.register(s)

    s.connect(url)
    
    msg = zmq.Message(b' ' * size)
    block = zmq.NOBLOCK if poll else 0
    
    for i in range(count):
        if poll:
            res = p.poll()
            assert(res[0][1] & zmq.POLLOUT)
        s.send(msg, block, copy=copy)

    s.close()
    ctx.term()

def throughput(url, count, size, poll, copy):
    """recv a bunch of messages on a PULL socket
    
    Should be started before `pusher`
    """
    ctx = zmq.Context()
    s = ctx.socket(zmq.PULL)

    #  Add your socket options here.
    #  For example ZMQ_RATE, ZMQ_RECOVERY_IVL and ZMQ_MCAST_LOOP for PGM.

    if poll:
        p = zmq.Poller()
        p.register(s)

    s.bind(url)

    block = zmq.NOBLOCK if poll else 0
    
    # Wait for the other side to connect.
    msg = s.recv()
    assert len (msg) == size
    
    start = now()
    for i in range (count-1):
        if poll:
            res = p.poll()
        msg = s.recv(block, copy=copy)
    elapsed = now() - start
    
    throughput = (float(count)) / float(elapsed)
    megabits = float(throughput * size * 8) / 1e6

    print ("message size   : %8i     [B]" % (size, ))
    print ("message count  : %8i     [msgs]" % (count, ))
    print ("mean throughput: %8.0f     [msg/s]" % (throughput, ))
    print ("mean throughput: %12.3f [Mb/s]" % (megabits, ))
    print ("test time      : %12.3f [s]" % (elapsed, ))


def main():
    args = parse_args()
    tic = time.time()
    if args.test == 'lat':
        bg = Process(target=latency_echo, args=(args.url, args.count, args.poll, args.copy))
        bg.start()
        latency(args.url, args.count, args.size, args.poll, args.copy)
    elif args.test == 'thr':
        bg = Process(target=throughput, args=(args.url, args.count, args.size, args.poll, args.copy))
        bg.start()
        pusher(args.url, args.count, args.size, args.poll, args.copy)
    bg.join()
    toc = time.time()
    if (toc - tic) < 3:
        print ("For best results, tests should take at least a few seconds.")

if __name__ == '__main__':
    main()
