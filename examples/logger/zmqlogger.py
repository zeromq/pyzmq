"""
Simple example of using zmq log handlers

This starts a number of subprocesses with PUBHandlers that generate
log messages at a regular interval.  The main process has a SUB socket,
which aggregates and logs all of the messages to the root logger.
"""

import logging
from multiprocessing import Process
import os
import random
import sys
import time

import zmq
from zmq.log.handlers import PUBHandler

LOG_LEVELS = (logging.DEBUG, logging.INFO,
              logging.WARN, logging.ERROR, logging.CRITICAL)


def sub_logger(port, level=logging.DEBUG):
    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.bind('tcp://127.0.0.1:%i' % port)
    sub.setsockopt(zmq.SUBSCRIBE, b"")
    logging.basicConfig(level=level)

    while True:
        level, message = sub.recv_multipart()
        message = message.decode('ascii')
        if message.endswith('\n'):
            # trim trailing newline, which will get appended again
            message = message[:-1]
        log = getattr(logging, level.lower().decode('ascii'))
        log(message)


def log_worker(port, interval=1, level=logging.DEBUG):
    ctx = zmq.Context()
    pub = ctx.socket(zmq.PUB)
    pub.connect('tcp://127.0.0.1:%i' % port)

    logger = logging.getLogger(str(os.getpid()))
    logger.setLevel(level)
    handler = PUBHandler(pub)
    logger.addHandler(handler)
    print("starting logger at %i with level=%s" % (os.getpid(), level))

    while True:
        level = random.choice(LOG_LEVELS)
        logger.log(level, "Hello from %i!" % os.getpid())
        time.sleep(interval)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    else:
        n = 2

    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        port = 5558

    # start the log generators
    workers = [Process(target=log_worker, args=(port,), kwargs=dict(level=random.choice(LOG_LEVELS)))
               for i in range(n)]
    [w.start() for w in workers]

    # start the log watcher
    try:
        sub_logger(port)
    except KeyboardInterrupt:
        pass
    finally:
        [w.terminate() for w in workers]
