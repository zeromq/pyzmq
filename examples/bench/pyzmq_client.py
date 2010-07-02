import zmq

c = zmq.Context()
s = c.socket(zmq.REQ)
s.connect('tcp://127.0.0.1:10001')

def echo(msg):
    s.send(msg, copy=False)
    msg2 = s.recv(copy=False)
    return msg2

class Client(object):
    pass

client = Client()
client.echo = echo
