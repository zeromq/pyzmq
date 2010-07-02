from SimpleXMLRPCServer import SimpleXMLRPCServer

def echo(x):
    return x

server = SimpleXMLRPCServer(('localhost',10002))
server.register_function(echo)
server.serve_forever()