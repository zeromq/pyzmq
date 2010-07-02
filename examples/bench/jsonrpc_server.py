from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

def echo(x):
    return x

server = SimpleJSONRPCServer(('localhost',10000))
server.register_function(echo)
server.serve_forever()