"""A PyZMQ based simple RPC service.

Authors:

* Brian Granger

Example
-------

To create a simple service::

    from zmq.rpc.simplerpc import RPCService, rpc_method

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
from zmq.eventloop.ioloop import IOLoop, DelayedCallback
from zmq.utils import jsonapi


#-----------------------------------------------------------------------------
# Serializer
#-----------------------------------------------------------------------------


class Serializer(object):
    """A class for serializing/deserializing objects."""

    def loads(self, s):
        return pickle.loads(s)

    def dumps(self, o):
        return pickle.dumps(o)

    def serialize_args_kwargs(self, args, kwargs):
        """Serialize args/kwargs into a msg list."""
        return self.dumps(args), self.dumps(kwargs)

    def deserialize_args_kwargs(self, msg_list):
        """Deserialize a msg list into args, kwargs."""
        return self.loads(msg_list[0]), self.loads(msg_list[1])

    def serialize_result(self, result):
        """Serialize a result into a msg list."""
        return [self.dumps(result)]

    def deserialize_result(self, msg_list):
        """Deserialize a msg list into a result."""
        return self.loads(msg_list[0])

PickleSerializer = Serializer

class JSONSerializer(Serializer):
    """A class for serializing using JSON."""

    def loads(self, s):
        return jsonapi.loads(s)

    def dumps(self, o):
        return jsonapi.dumps(o)


#-----------------------------------------------------------------------------
# RPC Service
#-----------------------------------------------------------------------------


class RPCBase(object):

    def __init__(self, loop=None, context=None, serializer=None):
        """Base class for RPC service and proxy.

        Parameters
        ==========
        loop : IOLoop
            An existing IOLoop instance, if not passed, then IOLoop.instance()
            will be used.
        context : Context
            An existing Context instance, if not passed, the Context.instance()
            will be used.
        serializer : Serializer
            An instance of a Serializer subclass that will be used to serialize
            and deserialize args, kwargs and the result.
        """
        self.loop = loop if loop is not None else IOLoop.instance()
        self.context = context if context is not None else zmq.Context.instance()
        self.socket = None
        self.stream = None
        self._serializer = serializer if serializer is not None else PickleSerializer()
        self.reset()

    #-------------------------------------------------------------------------
    # Public API
    #-------------------------------------------------------------------------

    def reset(self):
        """Reset the socket/stream."""
        if isinstance(self.socket, zmq.Socket):
            self.socket.close()
        self._create_socket()
        self.urls = []

    def bind(self, url):
        """Bind the service to a url of the form proto://ip:port."""
        self.urls.append(url)
        self.socket.bind(url)

    def connect(self, url):
        """Connect the service to a url of the form proto://ip:port."""
        self.urls.append(url)
        self.socket.connect(url)


class RPCService(RPCBase):
    """An RPC service that takes requests over a ROUTER socket."""

    def _create_socket(self):
        self.socket = self.context.socket(zmq.ROUTER)
        self.stream = ZMQStream(self.socket, self.loop)
        self.stream.on_recv(self._handle_request)

    def _handle_request(self, msg_list):
        """Handle an incoming request.

        The request is received as a multipart message:

        [ident, msg_id, method, <sequence of serialized args/kwargs>]

        The reply depends on if the call was successful or not:

        [ident, msg_id, 'SUCCESS', <sequece of serialized result>]
        [ident, msg_id, 'FAILURE', ename, evalue, traceback]

        Here the (ename, evalue, traceback) are utf-8 encoded unicode.
        """
        self.ident = msg_list[0]
        self.msg_id = msg_list[1]
        method = msg_list[2]
        args, kwargs = self._serializer.deserialize_args_kwargs(msg_list[3:])

        # Find and call the actual handler for message.
        handler = getattr(self, method, None)
        if handler is not None and getattr(handler, 'is_rpc_method', False):
            try:
                result = handler(*args, **kwargs)
            except:
                self._send_error()
            else:
                try:
                    presult = self._serializer.serialize_result(result)
                except:
                    self._send_error()
                else:
                    msg_list = [self.ident, self.msg_id, b'SUCCESS']
                    msg_list.extend(presult)
                    self.stream.send_multipart(msg_list)
        else:
            logging.error('Unknown RPC method: %s' % method)

    def _send_error(self):
        """Send an error reply."""
        etype, evalue, tb = sys.exc_info()
        self.stream.send(self.ident, zmq.SNDMORE)
        self.stream.send(self.msg_id, zmq.SNDMORE)
        self.stream.send(b'FAILURE', zmq.SNDMORE)
        self.stream.send_unicode(unicode(etype.__name__), zmq.SNDMORE)
        self.stream.send_unicode(unicode(evalue), zmq.SNDMORE)
        self.stream.send_unicode(unicode(traceback.format_exc(tb)))


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


class RPCServiceProxyBase(RPCBase):
    """A service proxy to for talking to an RPCService."""

    def _create_socket(self):
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, bytes(uuid.uuid4()))
        self._init_stream()

    def _init_stream(self):
        pass

    def _build_msg(self, method, args, kwargs):
        msg_id = bytes(uuid.uuid4())
        method = bytes(method)
        msg_list = [msg_id, method]
        msg_list.extend(self._serializer.serialize_args_kwargs(args, kwargs))
        return msg_id, msg_list


class AsyncRPCServiceProxy(RPCServiceProxyBase):
    """An asynchronous service proxy."""

    def __init__(self, loop=None, context=None, serializer=None):
        super(AsyncRPCServiceProxy, self).__init__(
            loop=loop, context=context,
            serializer=serializer
        )
        self._callbacks = {}

    def _init_stream(self):
        self.stream = ZMQStream(self.socket, self.loop)
        self.stream.on_recv(self._handle_reply)

    def _handle_reply(self, msg_list):
        msg_id = msg_list[0]
        status = msg_list[1]
        cb_eb_dc = self._callbacks.pop(msg_id, None) # (cb, eb) tuple
        if cb_eb_dc is not None:
            cb, eb, dc = cb_eb_dc
            # Stop the timeout if there was one.
            if dc is not None:
                dc.stop()
            if status == b'SUCCESS' and cb is not None:
                result = self._serializer.deserialize_result(msg_list[2:])
                try:
                    cb(result)
                except:
                    logging.error('Unexpected callback error', exc_info=True)
            elif status == b'FAILURE' and eb is not None:
                ename = msg_list[2].decode('utf-8')
                evalue = msg_list[3].decode('utf-8')
                tb = msg_list[4].decode('utf-8')
                try:
                    eb(ename, evalue, tb)
                except:
                    logging.error('Unexpected callback error', exc_info=True)

    #-------------------------------------------------------------------------
    # Public API
    #-------------------------------------------------------------------------

    def __getattr__(self, name):
        return AsyncRemoteMethod(self, name)

    def call(self, method, callback, errback, timeout, *args, **kwargs):
        """Call the remote method with *args and **kwargs.

        Parameters
        ----------
        method : str
            The name of the remote method to call.
        callback : callable
            The callable to call upon success or None. The result of the RPC
            call is passed as the single argument to the callback:
            `callback(result)`.
        errback : callable
            The callable to call upon a remote exception or None, The
            signature of this method is `errback(ename, evalue, tb)` where
            the arguments are passed as strings.
        timeout : int
            The number of milliseconds to wait before aborting the request.
            When a request is aborted, the errback will be called with an
            RPCTimeoutError. Set to 0 or a negative number to use an infinite
            timeout.
        args : tuple
            The tuple of arguments to pass as `*args` to the RPC method.
        kwargs : dict
            The dict of arguments to pass as `**kwargs` to the RPC method.
        """
        if not isinstance(timeout, int):
            raise TypeError("int expected, got %r" % timeout)
        if not (callback is None or callable(callback)):
            raise TypeError("callable or None expected, got %r" % callback)
        if not (errback is None or callable(errback)):
            raise TypeError("callable or None expected, got %r" % errback)

        msg_id, msg_list = self._build_msg(method, args, kwargs)
        self.stream.send_multipart(msg_list)

        # The following logic assumes that the reply won't come back too
        # quickly, otherwise the callbacks won't be in place in time. It should
        # be fine as this code should run very fast. This approach improves
        # latency we send the request ASAP.
        def _abort_request():
            cb_eb_dc = self._callbacks.pop(msg_id, None)
            if cb_eb_dc is not None:
                eb = cb_eb_dc[1]
                if eb is not None:
                    try:
                        raise RPCTimeoutError()
                    except:
                        etype, evalue, tb = sys.exc_info()
                        eb(etype.__name__, evalue, traceback.format_exc(tb))
        if timeout > 0:
            dc = DelayedCallback(_abort_request, timeout, self.loop)
            dc.start()
        else:
            dc = None

        self._callbacks[msg_id] = (callback, errback, dc)


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

        msg_id, msg_list = self._build_msg(method, args, kwargs)
        self.socket.send_multipart(msg_list)
        msg_list = self.socket.recv_multipart()
        msg_id = msg_list[0]
        status = msg_list[1]
        if status == b'SUCCESS':
            result = self._serializer.deserialize_result(msg_list[2:])
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

class RPCTimeoutError(Exception):
    pass
