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

    def handle_pyin(self, omsg):
        if omsg.msg_type != 'pyin':
            return
        if omsg.parent_header.session == self.session.session:
            return
        print '[IN from other]', omsg.parent_header.username
        print omsg.content.code

    def handle_pyout(self, omsg):
        if omsg.msg_type != 'pyout':
            return
        print ']]]', omsg.content.data

    def print_pyerr(self, err):
        print >> sys.stderr, err.etype,':', err.evalue
        print >> sys.stderr, ''.join(err.traceback)       

    def handle_pyerr(self, omsg):
        if omsg.msg_type != 'pyerr':
            return
        if omsg.parent_header.session == self.session.session:
            return
        print '[ERR from other]', omsg.parent_header.username
        self.print_pyerr(omsg.content)
        
    def handle_stream(self, omsg):
        if omsg.msg_type != 'stream':
            return
        if omsg.content.name == 'stdout':
            outstream = sys.stdout
        else:
            outstream = sys.stderr
            print >> outstream, '*** ERROR ***'
        print >> outstream, omsg.content.data,
        
    def recv_output(self):
        while True:
            msg = self.sub_socket.recv_json(zmq.NOBLOCK)
            omsg =  msg if msg is None else session.msg2obj(msg)
            if omsg is None:
                break
            # Filter, don't echo our own inputs back out
            self.handle_pyin(omsg)
            self.handle_pyout(omsg)
            self.handle_stream(omsg)

    def recv_reply(self):
        msg = self.request_socket.recv_json(zmq.NOBLOCK)
        obj =  msg if msg is None else session.msg2obj(msg)
        return obj
    
    def runcode(self, code):
        code = '\n'.join(self.buffer)
        msg = self.session.msg('execute_request', dict(code=code))
        self.request_socket.send_json(msg)
        
        for i in range(1000):
            self.recv_output()
            end = self.recv_reply()
            if end is not None:
                self.recv_output()
                if end.content.status == 'error':
                    self.print_pyerr(end.content)
                break
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
                               session, request_socket, sub_socket)
        
    def interact(self):
        self.console.interact()


if __name__ == '__main__':
    # Defaults
    ip = '192.168.2.109'
    ip = '127.0.0.1'
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
