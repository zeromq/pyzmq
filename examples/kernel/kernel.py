import sys
import time

import zmq


class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    def __init__(self, socket, name='stdout', max_buffer=200):
        self.socket = socket
        self.name = name
        self._buffer = []
        self._buffer_len = 0
        self.max_buffer = max_buffer

    def close(self):
        self.socket = None

    def flush(self):
        if self.socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            if self._buffer:
                content = ''.join(self._buffer)
                msg = dict(name=self.name, content=content)
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
        if self._buffer_len > self.max_buffer:
            self.flush()

    def writelines(self, sequence):
        if self.socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            content = ''.join(sequence)
            msg = dict(name=self.name, content=content)
            self.socket.send_json(msg)


def main():
    c = zmq.Context(1,1)

    reply = zmq.Socket(c, zmq.REP)
    reply.bind('tcp://127.0.0.1:5556')

    stream = zmq.Socket(c, zmq.PUB)
    stream.bind('tcp://127.0.0.1:5555')
    stdout = OutStream(stream, 'stdout')
    stderr = OutStream(stream, 'stderr')
    sys.stdout = stdout
    sys.stderr = stderr

    run = True
    user_ns = {}
    
    while run:
        action = reply.recv_json()
        code = action['code']
        try:
            exec code in user_ns, user_ns
        except:
            result = dict(success=False)
        else:
            result = dict(success=True)
        reply.send_json(result)


if __name__ == '__main__':
    main()
