import logging
import logging.config
import zmq
import multiprocessing
from zmq.eventloop import *

def sub_logger(port):
    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.connect('tcp://127.0.0.1:%i'%port)
    sub.setsockopt(zmq.SUBSCRIBE,"")
    while True:
        message = sub.recv_multipart()
        name = message[0]
        msg = message[1:]
        if name == 'log':
            msg[0] = int(msg[0])
        getattr(logging, name)(*msg)
        
    

class ZLogger(object):
    
    def __init__(self,fname=None):
        if fname is not None:
            logging.config.fileConfig(fname)
        self.ctx = zmq.Context()
        self.pub = self.ctx.socket(zmq.PUB)
        self.port = self.pub.bind_to_random_port('tcp://127.0.0.1')
        self.sub_proc = multiprocessing.Process(target=sub_logger, args=(self.port,))
        self.sub_proc.start()
        pass
    
    def log(self, level, msg):
        self.pub.send_multipart(['log', str(level), msg])
    
    def warn(self, msg):
        self.pub.send_multipart(['warn', msg])
    
    def error(self, msg):
        self.pub.send_multipart(['error', msg])
    



