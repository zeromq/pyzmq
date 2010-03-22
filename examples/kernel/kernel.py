import __builtin__
import sys
import time
import traceback
import uuid

import zmq

from session import KernelSession



def stream2msg(sender_id, msg_id, name, data):
    return dict(
        sender_id=sender_id,
        msg_id=msg_id,
        msg_type='stream',
        content=dict(
            name=name,
            data=data
        )
    )


class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    def __init__(self, socket, name='stdout', max_buffer=200):
        self.socket = socket
        self.name = name
        self._buffer = []
        self._buffer_len = 0
        self.max_buffer = max_buffer
        self.msg_id = 0
        self.sender_id = str(uuid.uuid4())

    def close(self):
        self.socket = None

    def flush(self):
        if self.socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            if self._buffer:
                data = ''.join(self._buffer)
                msg = stream2msg(self.sender_id, self.msg_id, self.name, data)
                print>>sys.__stdout__, repr(msg)
                self.msg_id += 1
                self.socket.send_json(msg)
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
        if self.socket is None:
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
        if self.socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            for s in sequence:
                self.write(s)


class DisplayHook(object):

    def __init__(self, socket):
        self.socket = socket
        self.sender_id = str(uuid.uuid4())
        self.msg_id = 0

    def __call__(self, obj):
        __builtin__._ = obj
        msg = dict(
            sender_id=self.sender_id,
            msg_id=self.msg_id,
            msg_type=u'pyout',
            content=dict(
                data=repr(obj)
            )
        )
        self.msg_id += 1
        self.socket.send_json(msg)


class RawInput(object):

    def __init__(self, socket):
        self.socket = socket

    def __call__(self, prompt=None):
        msg =  dict(
        
        )
        self.send_json(msg)
        reply = None
        while reply is None:
            reply = self.recv_json(zmq.NOBLOCK)
        return reply['content']['data']


class Kernel(object):

    def __init__(self, socket):
        self.socket = socket
        self.user_ns = {}
        self.history = []
        self.sender_id = str(uuid.uuid4())
        self.msg_id = 0

    def execute_request(self, ident, msg):
        code = msg[u'content'][u'code']
        try:
            exec code in self.user_ns, self.user_ns
        except:
            result = 'error'
            print>>sys.stderr, traceback.format_exc()
        else:
            result = 'ok'
        reply_msg = self.execute_reply(result, msg)
        print>>sys.__stdout__, "Reply: ", repr(reply_msg)
        self.socket.send_json(reply_msg, ident=ident)
        
    def execute_reply(self, result, msg):
        reply_msg = dict(
            sender_id=self.sender_id,
            msg_id=self.msg_id,
            parent_msg_id=msg[u'msg_id'],
            parent_sender_id=msg[u'sender_id'],
            msg_type=u'execute_reply',
            content=dict(
                data=result
            )
        )
        self.msg_id += 1
        return reply_msg

    def start(self):
        while True:
            # msg = self.socket.recv()
            # print>>sys.__stdout__, "Got msg: ", repr(msg)
            ident, msg = self.socket.recv_json(ident=True)
            print>>sys.__stdout__, "Got ident: ", repr(ident)
            print>>sys.__stdout__, "Got msg: ", msg
            if msg[u'msg_type'] == u'execute_request':
                self.execute_request(ident, msg)


def main():
    c = zmq.Context(1, 1)

    session = Session(username='kernel')

    reply = c.socket(zmq.XREP)
    reply.bind('tcp://192.168.2.109:5555')
    kernel = Kernel(reply)

    stream = c.socket(zmq.PUB)
    stream.bind('tcp://192.168.2.109:5556')
    stdout = OutStream(stream, 'stdout')
    stderr = OutStream(stream, 'stderr')
    sys.stdout = stdout
    sys.stderr = stderr



    print>>sys.__stdout__, "Starting the kernel..."
    kernel.start()


if __name__ == '__main__':
    main()

"""
* Make sender_id, msg_id global to the process.
* Figure out how to handle parent id stuff.
* Make a factory for blank messages of all types.
* raw_input

"""
