import zmq

url = "tcp://127.0.0.1:5555"
ctx = zmq.Context()
server_public, server_secret = zmq.curve_keypair()

# setup server socket (curve_server=True)
server = ctx.socket(zmq.PUSH)
server.curve_server = True
server.curve_secretkey = server_secret
server.bind(url)

# setup client socket (sets curve_serverkey)
client = ctx.socket(zmq.PULL)
client.curve_serverkey = server_public
client.curve_publickey, client.curve_secretkey = zmq.curve_keypair()
client.connect(url)

server.send(b"message")
client.recv()  # will not get a message if CURVE is not configured correctly
