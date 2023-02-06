import gevent

from zmq import green as zmq


# Connect to both receiving sockets and send 10 messages
def sender():
    sender = context.socket(zmq.PUSH)
    sender.connect('inproc://polltest1')
    sender.connect('inproc://polltest2')

    for i in range(10):
        sender.send('test %d' % i)
        gevent.sleep(1)


# create zmq context, and bind to pull sockets
context = zmq.Context()
receiver1 = context.socket(zmq.PULL)
receiver1.bind('inproc://polltest1')
receiver2 = context.socket(zmq.PULL)
receiver2.bind('inproc://polltest2')

gevent.spawn(sender)

# Create poller and register both receiver sockets
poller = zmq.Poller()
poller.register(receiver1, zmq.POLLIN)
poller.register(receiver2, zmq.POLLIN)

# Read 10 messages from both receiver sockets
msgcnt = 0
while msgcnt < 10:
    socks = dict(poller.poll())
    if receiver1 in socks and socks[receiver1] == zmq.POLLIN:
        print(f"Message from receiver1: {receiver1.recv()!r}")
        msgcnt += 1

    if receiver2 in socks and socks[receiver2] == zmq.POLLIN:
        print(f"Message from receiver2: {receiver2.recv()!r}")
        msgcnt += 1

print(f"{msgcnt} messages received")
