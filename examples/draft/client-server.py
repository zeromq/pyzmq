import time

import zmq

ctx = zmq.Context.instance()

url = 'tcp://127.0.0.1:5555'
server = ctx.socket(zmq.SERVER)
server.bind(url)

for i in range(10):
    client = ctx.socket(zmq.CLIENT)
    client.connect(url)
    client.send(f'request {i}'.encode("ascii"))
    msg = server.recv(copy=False)
    print(f'server recvd {msg.bytes!r} from {msg.routing_id!r}')
    server.send_string(f'reply {i}', routing_id=msg.routing_id)
    reply = client.recv_string()
    print(f'client recvd {reply!r}')
    time.sleep(0.1)
    client.close()

server.close()
ctx.term()
