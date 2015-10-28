"""Future-returning Socket for zmq"""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.


import zmq as _zmq
from zmq.eventloop.zmqstream import ZMQStream

from concurrent.futures import Future


class Socket(ZMQStream):
    
    _recv_futures = None
    _send_futures = None
    
    def __init__(self, context, socket_type, io_loop=None):
        socket = _zmq.Socket(context, socket_type)
        super(Socket, self).__init__(socket, io_loop=io_loop)
        self._recv_futures = []
        self._send_futures = []
        # drop inherited non-future APIs
        # del self.on_recv, self.on_recv_stream, self.stop_on_recv, \
        #     self.on_send, self.on_send_stream, self.stop_on_send, \
        #     self.on_err, self.stop_on_err
    
    def __getattr__(self, attr):
        return getattr(self.socket, attr)
    
    def __setattr__(self, attr, value):
        if not hasattr(self, attr):
            setattr(self.socket, attr, value)
        else:
            super(Socket, self).__setattr__(attr, value)
    
    def _handle_recv(self):
        f = None
        while self._recv_futures:
            f, multipart, kwargs = self._recv_futures.pop(0)
            # skip any cancelled futures
            if f.done():
                f = None
                continue
            else:
                break
        if f is not None:
            recv = self.socket.recv_multipart if multipart else self.socket.recv
            kwargs['flags'] |= _zmq.DONTWAIT
            try:
                result = recv(**kwargs)
            except Exception as e:
                f.set_exception(e)
            else:
                f.set_result(result)
        
        if not self._recv_futures:
            # stop triggering recv if no Futures are waiting
            self._drop_io_state(self.io_loop.READ)
        
    def recv_multipart(self, flags=0, copy=True, track=False):
        f = Future()
        self._recv_futures.append(
            (f, True, dict(flags=flags, copy=copy, track=track))
        )
        self._add_io_state(self.io_loop.READ)
        return f
    
    def recv(self, flags=0, copy=True, track=False):
        f = Future()
        self._recv_futures.append(
            (f, False, dict(flags=flags, copy=copy, track=track))
        )
        self._add_io_state(self.io_loop.READ)
        

class Context(_zmq.Context):
    @staticmethod
    def _socket_class(self, socket_type):
        return Socket(self, socket_type, io_loop=self.io_loop)

    