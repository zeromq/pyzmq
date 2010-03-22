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
        self.backgrounded = 0

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

    def _recv(self, socket):
        msg = socket.recv_json(zmq.NOBLOCK)
        omsg =  msg if msg is None else session.msg2obj(msg)
        return omsg

    def handle_output(self, omsg):
        # Filter, don't echo our own inputs back out
        self.handle_pyin(omsg)
        self.handle_pyout(omsg)
        self.handle_pyerr(omsg)
        self.handle_stream(omsg)

    def recv_output(self):
        while True:
            omsg = self._recv(self.sub_socket)
            if omsg is None:
                break
            self.handle_output(omsg)

    def recv_reply(self):
        return self._recv(self.request_socket)

    def runcode(self, code):
        # We can't pickle code objects, so fetch the actual source
        src = '\n'.join(self.buffer)

        # for non-background inputs, if we do have previoiusly backgrounded
        # jobs, check to see if they've produced results
        if not src.endswith(';'):
            while self.backgrounded > 0:
                #print 'checking background'
                rep = self.recv_reply()
                self.recv_output()
                if rep:
                    self.backgrounded -= 1
                time.sleep(0.1)

        # Send code execution message to kernel
        msg = self.session.msg('execute_request', dict(code=src))
        self.request_socket.send_json(msg)

        # Fake asynchronicity by letting the user put ';' at the end of the line
        if src.endswith(';'):
            self.backgrounded += 1
            return

        # For foreground jobs, wait for reply
        while True:
            end = self.recv_reply()
            if end is not None:
                self.recv_output()
                if end.content.status == 'error':
                    self.print_pyerr(end.content)
                break
            self.recv_output()
            time.sleep(0.05)
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
    #ip = '127.0.0.1'
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
