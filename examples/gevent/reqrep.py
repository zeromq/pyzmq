"""
Complex example which is a combination of the rr* examples from the zguide.
"""
from gevent import spawn
import zmq.green as zmq

# server
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect("tcp://localhost:5560")

def serve(socket):
    while True:
        message = socket.recv()
        print "Received request: ", message
        socket.send("World")
server = spawn(serve, socket)


# client
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5559")

#  Do 10 requests, waiting each time for a response
def client():
    for request in range(1,10):
        socket.send("Hello")
        message = socket.recv()
        print "Received reply ", request, "[", message, "]"


# broker
frontend = context.socket(zmq.XREP)
backend  = context.socket(zmq.XREQ);
frontend.bind("tcp://*:5559")
backend.bind("tcp://*:5560")

def proxy(socket_from, socket_to):
    while True:
        m = socket_from.recv_multipart()
        socket_to.send_multipart(m)

a = spawn(proxy, frontend, backend)
b = spawn(proxy, backend, frontend)

spawn(client).join()
