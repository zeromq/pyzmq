import __builtin__
import sys
import traceback

from code import CommandCompiler

import zmq

from session import Session, msg2obj, extract_header


class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    def __init__(self, session, pub_socket, name, max_buffer=200):
        self.session = session
        self.pub_socket = pub_socket
        self.name = name
        self._buffer = []
        self._buffer_len = 0
        self.max_buffer = max_buffer
        self.parent_header = {}

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    def flush(self):
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        else:
            if self._buffer:
                data = ''.join(self._buffer)
                content = {u'name':self.name, u'data':data}
                msg = self.session.msg(u'stream', content=content, parent=self.parent_header)
                print>>sys.__stdout__, repr(msg)
                self.pub_socket.send_json(msg)
                self._buffer_len = 0
                self._buffer = []

    def isattr(self):
        return False

    def next(self):
        raise IOError('Read not supported on a write only stream.')

    def read(self, size=None):
        raise IOError('Read not supported on a write only stream.')

    readline=read

    def write(self, s):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            self._buffer.append(s)
            self._buffer_len += len(s)
            self._maybe_send()

    def _maybe_send(self):
        if '\n' in self._buffer[-1]:
            self.flush()
        if self._buffer_len > self.max_buffer:
            self.flush()

    def writelines(self, sequence):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            for s in sequence:
                self.write(s)


class DisplayHook(object):

    def __init__(self, session, pub_socket):
        self.session = session
        self.pub_socket = pub_socket
        self.parent_header = {}

    def __call__(self, obj):
        __builtin__._ = obj
        msg = self.session.msg(u'pyout', {u'data':repr(obj)}, parent=self.parent_header)
        self.pub_socket.send_json(msg)

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)


class RawInput(object):

    def __init__(self, session, socket):
        self.session = session
        self.socket = socket

    def __call__(self, prompt=None):
        msg = self.session.msg(u'raw_input')
        self.send_json(msg)
        reply = None
        while reply is None:
            reply = self.recv_json(zmq.NOBLOCK)
        return reply[u'content'][u'data']


class Kernel(object):

    def __init__(self, session, reply_socket, pub_socket):
        self.session = session
        self.reply_socket = reply_socket
        self.pub_socket = pub_socket
        self.user_ns = {}
        self.history = []
        self.compiler = CommandCompiler()

    def execute_request(self, ident, parent):
        try:
            code = parent[u'content'][u'code']
        except:
            print>>sys.__stderr__, "Got bad msg: ", parent
            return
        pyin_msg = self.session.msg(u'pyin',{u'code':code}, parent=parent)
        self.pub_socket.send_json(pyin_msg)
        try:
            comp_code = self.compiler(code, '<zmq-kernel>')
            exec comp_code in self.user_ns, self.user_ns
        except:
            result = u'error'
            etype, evalue, tb = sys.exc_info()
            tb = traceback.format_exception(etype, evalue, tb)
            exc_content = {
                u'status' : u'error',
                u'traceback' : tb,
                u'etype' : unicode(etype),
                u'evalue' : unicode(evalue)
            }
            exc_msg = self.session.msg(u'pyerr', exc_content, parent)
            self.pub_socket.send_json(exc_msg)
            reply_content = exc_content
        else:
            reply_content = {'status' : 'ok'}
        reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        print>>sys.__stdout__, "Reply: ", repr(reply_msg)
        self.reply_socket.send_json(reply_msg, ident=ident)

    def start(self):
        while True:
            ident, msg = self.reply_socket.recv_json(ident=True)
            print>>sys.__stdout__, "Got ident: ", repr(ident)
            print>>sys.__stdout__, "Got msg: ", msg
            if msg[u'msg_type'] == u'execute_request':
                self.execute_request(ident, msg)


def main():
    c = zmq.Context(1, 1)

    ip = '192.168.2.109'
    ip = '127.0.0.1'
    port_base = 5555
    connection = ('tcp://%s' % ip) + ':%i'
    rep_conn = connection % port_base
    pub_conn = connection % (port_base+1)

    session = Session(username=u'kernel')

    reply_socket = c.socket(zmq.XREP)
    reply_socket.bind(rep_conn)

    pub_socket = c.socket(zmq.PUB)
    pub_socket.bind(pub_conn)

    stdout = OutStream(session, pub_socket, u'stdout')
    stderr = OutStream(session, pub_socket, u'stderr')
    sys.stdout = stdout
    # sys.stderr = stderr

    display_hook = DisplayHook(session, pub_socket)
    sys.displayhook = display_hook

    kernel = Kernel(session, reply_socket, pub_socket)

    print>>sys.__stdout__, "Starting the kernel..."
    kernel.start()


if __name__ == '__main__':
    main()


