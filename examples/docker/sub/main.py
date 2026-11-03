# BSD 3-Clause License
# Stef van der Struijk

import argparse
import zmq


def subscriber(ip="0.0.0.0", port=5551):
    # ZMQ connection
    url = "tcp://{}:{}".format(ip, port)
    print("Going to bind to: {}".format(url))
    ctx = zmq.Context()
    socket = ctx.socket(zmq.SUB)
    socket.bind(url)  # subscriber creates ZeroMQ socket
    socket.setsockopt(zmq.SUBSCRIBE, ''.encode('ascii'))  # any topic
    print("Sub bound to: {}\nWaiting for data...".format(url))

    while True:
        # wait for publisher data
        topic, msg = socket.recv_multipart()
        print("On topic {}, received data: {}".format(topic, msg))


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
    subscriber(**vars(args))
