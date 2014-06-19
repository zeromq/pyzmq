"""The prompt part of a simply two process chat app."""

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

def main(addr, account):

    ctx = zmq.Context()
    socket = ctx.socket(zmq.PUB)
    socket.bind(addr)

    while True:
        message = raw_input("%s> " % account)
        socket.send_multipart((account, message))


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print "usage: prompt.py <address> <username>"
        raise SystemExit
    main(sys.argv[1], sys.argv[2])
