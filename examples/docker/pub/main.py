# BSD 3-Clause License
# Stef van der Struijk

import argparse
import zmq
import time


def publisher(ip="0.0.0.0", port=5551):
    # ZMQ connection
    url = "tcp://{}:{}".format(ip, port)
    print("Going to connect to: {}".format(url))
    ctx = zmq.Context()
    socket = ctx.socket(zmq.PUB)
    socket.connect(url)  # publisher connects to subscriber
    print("Pub connected to: {}\nSending data...".format(url))

    i = 0

    while True:
        topic = 'foo'.encode('ascii')
        msg = 'test {}'.format(i).encode('ascii')
        # publish data
        socket.send_multipart([topic, msg])  # 'test'.format(i)
        print("On topic {}, send data: {}".format(topic, msg))
        time.sleep(.5)

        i += 1


if __name__ == "__main__":
    # command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=argparse.SUPPRESS,
                        help="IP of (Docker) machine")
    parser.add_argument("--port", default=argparse.SUPPRESS,
                        help="Port of (Docker) machine")

    args, leftovers = parser.parse_known_args()
    print("The following arguments are used: {}".format(args))
    print("The following arguments are ignored: {}\n".format(leftovers))

    # call function and pass on command line arguments
    publisher(**vars(args))
