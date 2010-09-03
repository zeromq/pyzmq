"""A client for the device based server."""

#
#    Copyright (c) 2010 Brian E. Granger and Eugene Chernyshov
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import zmq
import os
from time import time

print 'Client', os.getpid()

context = zmq.Context(1)

socket = context.socket(zmq.REQ)
socket.connect('tcp://127.0.0.1:5555')

while True:
    data = zmq.Message(str(os.getpid()))
    start = time()
    socket.send(data)
    data = socket.recv()
    print time()-start, data

