from timeit import default_timer as timer
from jsonrpclib import Server

client = Server('http://localhost:10000')
