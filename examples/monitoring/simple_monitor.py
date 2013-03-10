# -*- coding: utf-8 -*-
"""Simple example demonstrating the use of the socket monitoring feature.
"""

__license__ = '''
    This file is part of pyzmq.

    pyzmq is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pyzmq is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    Lesser GNU General Public License for more details.

    You should have received a copy of the Lesser GNU General Public License
    along with pyzmq.  If not, see <http://www.gnu.org/licenses/>.
'''

__author__ = 'Guido Goldstein'
__email__ = 'gst-py@a-nugget.de'
__version__ = '0.0'


import sys
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

zmq_ctx = zmq.Context()

s_rep = zmq_ctx.socket(zmq.REP)
s_rep.linger =0

s_req = zmq_ctx.socket(zmq.REQ)
s_req.linger = 0

s_req.monitor("inproc://monitor.req", zmq.EVENT_ALL)
s_event = s_req.get_monitor_socket()
s_event.linger = 0

t = threading.Thread(target=logger)
t.start()

print "bind"
s_req.bind("tcp://192.168.1.4:6666")
time.sleep(1)

print "connect"
s_rep.connect("tcp://192.168.1.4:6666")
time.sleep(2.0)

print "disconnect"
s_rep.disconnect("tcp://192.168.1.4:6666")
## s_rep.close()
time.sleep(2.0)
print "---"
s_req.close()
time.sleep(2.0)
print "---"

time.sleep(5.0)
t.join()
del t

print "END"
