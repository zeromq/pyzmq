import sys
import time

import zmq

def main():
    ctx = zmq.Context()
    s = ctx.socket(zmq.REQ)
    s.connect('tcp://127.0.0.1:5555')

    for i in range(10):
        print "Making request..."
        s.send('message%i' % i)
        print "Sleeping 2 seconds..."
        time.sleep(2)
        print "Receiving reply..."
        msg = s.recv()
        print "Got reply: ", msg

if __name__ == '__main__':
    main()