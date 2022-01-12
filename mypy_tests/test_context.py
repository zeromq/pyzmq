import zmq

ctx = zmq.Context.instance()
s = ctx.socket(zmq.PUSH)
s.send(b"buf")
ctx2 = zmq.Context.shadow_pyczmq(123)
s2 = ctx2.socket(zmq.PUSH)
s.send(b"buf")
