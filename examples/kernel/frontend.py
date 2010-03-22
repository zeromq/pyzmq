"""A simple interactive frontend that talks to a kernel over 0mq.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import cPickle as pickle
import code
import uuid

# our own
import zmq

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
def code2msg(sender_id, msg_id, msg_type, code):
    """Return a message for a code object"""
    return dict(sender_id=sender_id, msg_id=msg_id, msg_type=msg_type,
                content=dict(code=pickle.dumps(code, -1)))


class Console(code.InteractiveConsole):
    msg_id = 0
    sender_id = uuid.uuid4()

    def __init__(self, locals=None, filename="<console>",
                 request_socket=None,
                 output_socket=None):
        code.InteractiveConsole(locals, filename)
        self.request_socket = request_socket
        self.output_socket = output_socket

    def recv_output(outlist):
        out = self.output_socket.recv_json(zmq.NOBLOCK)
        if out is not None:
            outlist.append(out)
    
    def runcode(self, code):
        self.msg_id += 1
        msg = code2msg(sender_id, msg_id, 'execute_request', code)
        self.request_socket.send_json(msg)
        out = []
        for i in range(10):
            self.recv_output()
            end = self.request_socket.recv(zmq.NOBLOCK)
            if end is not None:
                self.recv_output()
                break
            time.sleep(0.1)
        else:
            # We exited without hearing back from the kernel!
            print 'ERROR!!! kernel never got back to us!!!'
        print 'OUTPUT:'
        print '\n'.join(out)
                
                
#def main():
if __name__ == '__main__'
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
    
    output_socket = c.socket(zmq.SUB)
    output_socket.connection(sub_conn)
    output_socket.setsockopt(zmq.SUBSCRIBE, '')

    console = Console(None, '<0mq-console>', request_socket, output_socket)
    console.interact()
