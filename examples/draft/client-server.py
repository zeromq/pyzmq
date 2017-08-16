import time
import zmq

ctx = zmq.Context.instance()

url = 'tcp://127.0.0.1:5555'
server = ctx.socket(zmq.SERVER)
server.bind(url)

for i in range(10):
    client = ctx.socket(zmq.CLIENT)
    client.connect(url)
    client.send(b'request %i' % i)
    msg = server.recv(copy=False)
    print('server recvd %r from %r' % (msg.bytes, msg.routing_id))
    server.send_string('reply %i' % i, routing_id=msg.routing_id)
    reply = client.recv_string()
    print('client recvd %r' % reply)
    time.sleep(0.1)
    client.close()

server.close()
ctx.term()

