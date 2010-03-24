"""Tab-completion over zmq"""

import readline
import rlcompleter
import time

import session

class KernelCompleter(object):
    """Kernel-side completion machinery."""
    def __init__(self, namespace):
        self.namespace = namespace
        self.completer = rlcompleter.Completer(namespace)

    def complete(): pass
    
class ClientCompleter(object):
    """Client-side completion machinery.

    How it works: self.complete will be called multiple times, with
    state=0,1,2,... When state=0 it should compute ALL the completion matches,
    and then return them for each value of state."""
    
    def __init__(self, session, socket):
        self.session = session
        self.socket = socket
        self.matches = []
    
    def complete(self, text, state):
        # Get full line to give to the kernel in case it wants more info.
        
        line = readline.get_line_buffer()
        #print 'Completing client-side for:', line, text, state # dbg

        # send completion request to kernel
        msg = self.session.msg('complete_request',
                               dict(text=text, line=line))
        self.socket.send_json(msg)
        omsg = session.Messages(msg)
        self.messages[omsg.header.msg_id] = omsg

        # Give the kernel up to 1s to respond
        for i in range(10):
            rep = self.socket.recv_json(
        
        if state==0:
            self.matches = ['a','b','c']
        try:
            return self.matches[state]
        except IndexError:
            return None
