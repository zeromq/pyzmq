"""The display part of a simply two process chat app."""

#
#    Copyright (c) 2010 Andrew Gwozdziewycz
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

def main(addrs):
    
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, "")
    for addr in addrs:
        print "Connecting to: ", addr
        socket.connect(addr)

    while True:
        msg = socket.recv_pyobj()
        print "%s: %s" % (msg[1], msg[0])

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print "usage: display.py <address> [,<address>...]"
        raise SystemExit
    main(sys.argv[1:])
