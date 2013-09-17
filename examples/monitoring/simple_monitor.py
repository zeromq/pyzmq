# -*- coding: utf-8 -*-
"""Simple example demonstrating the use of the socket monitoring feature.
"""

__license__ = '''
    This file is part of pyzmq.

    Distributed under the terms of the New BSD License. The full
    license is in the file COPYING.BSD, distributed as part of this
    software.
'''

__author__ = 'Guido Goldstein'

import sys
import os
import time
import struct
import threading

import zmq
from zmq.utils.monitor import get_monitor_message


def logger():
    global s_event
    done = False
    time.sleep(1.0)
    while not done:
        done = s_event.poll(timeout=5000) == 0
        if not done:
            emsg = get_monitor_message(s_event)
            print emsg['event'], emsg['value'], repr(emsg['endpoint'])
            if emsg['event'] == 128:
                done = True
    print
    print "Logger done!"
    return

version = zmq.zmq_version_info()
print repr(version)
if version < (3,3,0):
    raise RuntimeError("Libzmq versions < 3.3 are not supported at the moment!")

zmq_ctx = zmq.Context()

s_rep = zmq_ctx.socket(zmq.REP)
s_rep.linger = 0

s_req = zmq_ctx.socket(zmq.REQ)
s_req.linger = 0

s_req.monitor("inproc://monitor.req", zmq.EVENT_ALL)
s_event = s_req.get_monitor_socket()
s_event.linger = 0

t = threading.Thread(target=logger)
t.start()

print "bind req"
s_req.bind("tcp://127.0.0.1:6666")
s_req.bind("tcp://127.0.0.1:6667")
time.sleep(1)

print "connect rep"
s_rep.connect("tcp://127.0.0.1:6667")
time.sleep(0.2)
s_rep.connect("tcp://127.0.0.1:6666")
time.sleep(2)

print "disconnect rep"
s_rep.disconnect("tcp://127.0.0.1:6667")
time.sleep(0.33)
s_rep.disconnect("tcp://127.0.0.1:6666")
time.sleep(2)
print "---"
print "close rep"
s_rep.close()
time.sleep(2)
print "---"
print "close req"
s_req.close()
time.sleep(2.0)
print "---"

t.join()
print "joined"

print "END"
zmq_ctx.destroy(0)
