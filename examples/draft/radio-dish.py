import time

import zmq

ctx = zmq.Context.instance()
radio = ctx.socket(zmq.RADIO)
dish = ctx.socket(zmq.DISH)
dish.rcvtimeo = 1000

dish.bind('udp://*:5556')
dish.join('numbers')
radio.connect('udp://127.0.0.1:5556')

for i in range(10):
    time.sleep(0.1)
    radio.send(f'{i:03}'.encode('ascii'), group='numbers')
    try:
        msg = dish.recv(copy=False)
    except zmq.Again:
        print('missed a message')
        continue
    print(f"Received {msg.group}:{msg.bytes.decode('utf8')}")

dish.close()
radio.close()
ctx.term()
