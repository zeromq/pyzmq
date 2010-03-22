"""A simple interactive frontend that talks to a kernel over 0mq.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import cPickle as pickle
import code
import readline
import sys
import time
import uuid

# our own
import zmq
import session

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class Console(code.InteractiveConsole):

    def __init__(self, locals=None, filename="<console>",
                 session = session,
                 request_socket=None,
                 sub_socket=None):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.session = session
        self.request_socket = request_socket
        self.sub_socket = sub_socket
        
    def recv_output(self):
        out = session.msg2obj(self.sub_socket.recv_json(zmq.NOBLOCK))
        if out is not None:
            print ']]]', out.content.data

    def recv_reply(self):
        return session.msg2obj(self.request_socket.recv_json(zmq.NOBLOCK))
    
    def runcode(self, code):
        code = '\n'.join(self.buffer)
        msg = self.session.msg('execute_request', code)
        self.request_socket.send_json(msg)
        
        for i in range(1000):
            end = self.recv_reply()
            if end is not None:
                if end.content.data == 'error':
                    print >> sys.stderr, 'ERROR'
                self.recv_output()
                break
            self.recv_output()
            time.sleep(0.1)
        else:
            # We exited without hearing back from the kernel!
            print >> sys.stderr, 'ERROR!!! kernel never got back to us!!!'


class InteractiveClient(object):
    def __init__(self, session, request_socket, sub_socket):
        self.session = session
        self.request_socket = request_socket
        self.sub_socket = sub_socket
        self.console = Console(None, '<0mq-console>',
                               request_socket, sub_socket)
        
    def interact(self):
        self.console.interact()


if __name__ == '__main__':
    # Defaults
    ip = '192.168.2.109'
    port_base = 5555
    connection = ('tcp://%s' % ip) + ':%i'
    req_conn = connection % port_base
    sub_conn = connection % (port_base+1)
    
    # Create initial sockets
    c = zmq.Context()
    request_socket = c.socket(zmq.XREQ)
    request_socket.connect(req_conn)
    
    sub_socket = c.socket(zmq.SUB)
    sub_socket.connect(sub_conn)
    sub_socket.setsockopt(zmq.SUBSCRIBE, '')

    # Make session and user-facing client
    sess = session.Session()
    client = InteractiveClient(sess, request_socket, sub_socket)
    client.interact()

"""
import time
x = 2
for i in range(5):
    print x**i
    time.sleep(1)


import numpy as np
n = 800
a = np.random.uniform(size=(n,n))
a = a+a.T
e = np.linalg.eig(a)
"""
