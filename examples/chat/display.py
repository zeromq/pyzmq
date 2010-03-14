import zmq


def main(addr):
    print addr
    context = zmq.Context(1, 1)
    socket = context.socket(zmq.SUB)

    socket.setsockopt(zmq.SUBSCRIBE, "")
    socket.connect(addr)

    while True:
        msg = socket.recv_pyobj()
        print "%s: %s" % (msg[1], msg[0])

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print "usage: display.py <address>"
        raise SystemExit
    main(sys.argv[1])
