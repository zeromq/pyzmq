import zmq

ctx = zmq.Context()

url = "tcp://127.0.0.1:5555"
pub = ctx.socket(zmq.PUB)
sub = ctx.socket(zmq.SUB)
pub.bind(url)
sub.connect(url)
sub.subscribe(b"topic")
pub.send_multipart([b"topic", b"Message"])

msg = sub.recv()
print(msg.decode("utf8"))
more = sub.RCVMORE
assert more

msg = sub.recv(zmq.NOBLOCK)
assert msg == b"Message"

pub.close()
sub.close()
assert msg

assert sub.IDENTITY == b"abc"
