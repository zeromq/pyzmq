"""A PyZMQ based simple RPC service.

Authors:

* Brian Granger

Example
-------

To create a simple service::

    from zqm.rpc.simplerpc import RPCService, rpc_method

    class Echo(RPCService):

        @rpc_method
        def echo(self, s):
            return s

    if __name__ == '__main__':
        echo = Echo()
        echo.bind('tcp://127.0.0.1:5555')
        echo.start()

To talk to this service::

    from basicnbserver.rpc import BlockingRPCServiceProxy
    p = RPCServiceProxy()
    p.connect('tcp://127.0.0.1:5555')
    p.echo('Hi there')
    'Hi there'
"""

#-----------------------------------------------------------------------------
#
#    Copyright (c) 2010 Min Ragan-Kelley, Brian Granger
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import logging
try:
    import cPickle as pickle
except ImportError:
    import pickle
import sys
import traceback
import uuid

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop


#-----------------------------------------------------------------------------
# RPC Service
#-----------------------------------------------------------------------------


class RPCService(object):
    """An RPC service that takes requests over a ROUTER socket."""

    def __init__(self, loop=None, context=None):
        self.loop = loop if loop is not None else IOLoop.instance()
        self.context = context if context is not None else zmq.Context.instance()
        self._ready = False

    def _split_url(self):
        proto, ip, port = self.url.split(':')
        self.proto = proto
        self.ip = ip.lstrip('/')
        self.port = int(port)

    def bind(self, url):
        """Bind the service to proto://ip:port."""
        self.url = url
        self._split_url()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.bind(self.url)
        self.stream = ZMQStream(self.socket, self.loop)
        self.stream.on_recv(self.handle_request)
        self._ready = True

    def connect(self, url):
        """Connect the service to proto://ip:port."""
        self.url = url
        self._split_url()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.connect(self.url)
        self.stream = ZMQStream(self.socket, self.loop)
        self.stream.on_recv(self.handle_request)
        self._ready = True

    def handle_request(self, msg_list):
        """Handle an incoming request.

        The request is received as a multipart message:

        [ident, msg_id, method, pickle.dumps(args), pickle.dumps(kwargs)]

        The reply depends on if the call was successful or not:

        [ident, msg_id, 'SUCCESS', pickle.dumps(result)]
        [ident, msg_id, 'FAILURE', ename, evalue, traceback]

        Here the (ename, evalue, traceback) are utf-8 encoded unicode.
        """
        self.ident = msg_list[0]
        self.msg_id = msg_list[1]
        method = msg_list[2]
        args = pickle.loads(msg_list[3])
        kwargs = pickle.loads(msg_list[4])

        # Find and call the actual handler for message.
        handler = getattr(self, method, None)
        if handler is not None and getattr(handler, 'is_rpc_method', False):
            try:
                result = handler(*args, **kwargs)
            except:
                self.send_error()
            else:
                try:
                    presult = pickle.dumps(result)
                except:
                    self.send_error()
                else:
                    self.stream.send(self.ident, zmq.SNDMORE)
                    self.stream.send(self.msg_id, zmq.SNDMORE)
                    self.stream.send(b'SUCCESS', zmq.SNDMORE)
                    self.stream.send(presult)
        else:
            logging.error('Unknown RPC method: %s' % method)

    def send_error(self):
        """Send an error reply."""
        etype, evalue, tb = sys.exc_info()
        self.stream.send(self.ident, zmq.SNDMORE)
        self.stream.send(self.msg_id, zmq.SNDMORE)
        self.stream.send(b'FAILURE', zmq.SNDMORE)
        self.stream.send_unicode(unicode(etype.__name__), zmq.SNDMORE)
        self.stream.send_unicode(unicode(evalue), zmq.SNDMORE)
        self.stream.send_unicode(unicode(traceback.format_exc(tb)))

    def start(self):
        """Start the service."""
        if self._ready:
            self.loop.start()
        else:
            raise RuntimeError('bind or connect must be called before start')

    
def rpc_method(f):
    """A decorator for use in declaring a method as an rpc method.

    Use as follows::

        @rpc_method
        def echo(self, s):
            return s
    """
    f.is_rpc_method = True
    return f


#-----------------------------------------------------------------------------
# RPC Service Proxy
#-----------------------------------------------------------------------------


class RPCServiceProxyBase(object):
    """A service proxy to for talking to an RPCService."""

    def __init__(self, loop=None, context=None):
        self.loop = loop if loop is not None else IOLoop.instance()
        self.context = context if context is not None else zmq.Context.instance()
        self._ready = False

    def _split_url(self):
        proto, ip, port = self.url.split(':')
        self.proto = proto
        self.ip = ip.lstrip('/')
        self.port = int(port)

    def bind(self, url):
        """Bind the service proxy to proto://ip:port."""
        self.url = url
        self._split_url()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.bind(self.url)
        self.socket.setsockopt(zmq.IDENTITY, bytes(uuid.uuid4()))
        self.init_stream()
        self._ready = True

    def connect(self, url):
        """Connect the service to proto://ip:port."""
        self.url = url
        self._split_url()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(self.url)
        self.socket.setsockopt(zmq.IDENTITY, bytes(uuid.uuid4()))
        self.init_stream()
        self._ready = True

    def init_stream(self):
        pass


class AsyncRPCServiceProxy(RPCServiceProxyBase):
    """An asynchronous service proxy."""

    def __init__(self, loop=None, context=None):
        super(AsyncRPCServiceProxy, self).__init__(loop=loop, context=context)
        self._callbacks = {}

    def init_stream(self):
        self.stream = ZMQStream(self.socket, self.loop)
        self.stream.on_recv(self.handle_reply)

    def call(self, method, callback, *args, **kwargs):
        """Call the remote method with *args and **kwargs.

        Parameters
        ----------
        method : str
            The name of the remote method to call.
        callback : callable
            The callable call. The result of the RPC call is passed as 
            the single argument to the callback: `callback(result)`. If
            the call failed, result will be an instance of `RemoteRPCError`.
        args : tuple
            The tuple of arguments to pass as `*args` to the RPC method.
        kwargs : dict
            The dict of arguments to pass as `**kwargs` to the RPC method.
        """
        if not self._ready:
            raise RuntimeError('bind or connect must be called first')
        method = bytes(method)
        pargs = pickle.dumps(args)
        pkwargs = pickle.dumps(kwargs)
        msg_id = bytes(uuid.uuid4())
        self.stream.send(msg_id, zmq.SNDMORE)
        self.stream.send(method, zmq.SNDMORE)
        self.stream.send(pargs, zmq.SNDMORE)
        self.stream.send(pkwargs)
        self._callbacks[msg_id] = callback

    def handle_reply(self, msg_list):
        msg_id = msg_list[0]
        status = msg_list[1]
        if status == b'SUCCESS':
            result = pickle.loads(msg_list[2])
        elif status == b'FAILURE':
            ename = msg_list[2].decode('utf-8')
            evalue = msg_list[3].decode('utf-8')
            tb = msg_list[4].decode('utf-8')
            result = RemoteRPCError(ename, evalue, tb)

        cb = self._callbacks.get(msg_id)
        if cb is not None:
            try:
                cb(result)
            except:
                self.log.error('Unexpected callback error', exc_info=True)

    def __getattr__(self, name):
        return AsyncRemoteMethod(self, name)


class RPCServiceProxy(RPCServiceProxyBase):
    """A synchronous service proxy whose requests will block."""

    def call(self, method, *args, **kwargs):
        """Call the remote method with *args and **kwargs.

        Parameters
        ----------
        method : str
            The name of the remote method to call.
        args : tuple
            The tuple of arguments to pass as `*args` to the RPC method.
        kwargs : dict
            The dict of arguments to pass as `**kwargs` to the RPC method.

        Returns
        -------
        result : object
            If the call succeeds, the result of the call will be returned.
            If the call fails, `RemoteRPCError` will be raised.
        """
        if not self._ready:
            raise RuntimeError('bind or connect must be called first')
        method = bytes(method)
        pargs = pickle.dumps(args)
        pkwargs = pickle.dumps(kwargs)
        msg_id = bytes(uuid.uuid4())
        self.socket.send(msg_id, zmq.SNDMORE)
        self.socket.send(method, zmq.SNDMORE)
        self.socket.send(pargs, zmq.SNDMORE)
        self.socket.send(pkwargs)
        msg_list = self.socket.recv_multipart()
        msg_id = msg_list[0]
        status = msg_list[1]
        if status == b'SUCCESS':
            result = pickle.loads(msg_list[2])
            return result
        elif status == b'FAILURE':
            ename = msg_list[2].decode('utf-8')
            evalue = msg_list[3].decode('utf-8')
            tb = msg_list[3].decode('utf-8')
            raise RemoteRPCError(ename, evalue, tb)

    def __getattr__(self, name):
        return RemoteMethod(self, name)


class RemoteMethodBase(object):
    """A remote method class to enable a nicer call syntax."""

    def __init__(self, proxy, method):
        self.proxy = proxy
        self.method = method    


class AsyncRemoteMethod(RemoteMethodBase):

    def __call__(self, callback, *args, **kwargs):
        return self.proxy.call(self.method, callback, *args, **kwargs)


class RemoteMethod(RemoteMethodBase):

    def __call__(self, *args, **kwargs):
        return self.proxy.call(self.method, *args, **kwargs)


class RemoteRPCError(Exception):
    """Error raised elsewhere"""
    ename=None
    evalue=None
    traceback=None
    
    def __init__(self, ename, evalue, traceback):
        self.ename=ename
        self.evalue=evalue
        self.traceback=traceback
        self.args=(ename, evalue)
    
    def __repr__(self):
        return "<RemoteError:%s(%s)>" % (self.ename, self.evalue)

    def __str__(self):
        sig = "%s(%s)"%(self.ename, self.evalue)
        if self.traceback:
            return sig + '\n' + self.traceback
        else:
            return sig

