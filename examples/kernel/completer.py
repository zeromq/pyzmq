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

    def request_completion(self, text):
        line = readline.get_line_buffer()
        # send completion request to kernel
        msg = self.session.send(self.socket,
                                'complete_request',
                                dict(text=text, line=line))

        # Give the kernel up to 1s to respond
        for i in range(10):
            rep = self.session.recv(self.socket)
            if msg is not None:
                matches = ['a','b','c']  # dbg
            time.sleep(0.1)
        else:
            # timeout
            matches = None
        return matches
    
    def complete(self, text, state):
        # Get full line to give to the kernel in case it wants more info.
        if state==0:
            matches = self.request_completion(text)
            if matches is None:
                self.matches = []
                print >> sys.stderr, 'WARNING: Kernel timeout on tab completion.'
            else:
                self.matches = matches

        try:
            return self.matches[state]
        except IndexError:
            return None
