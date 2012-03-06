"""Base classes derived from tornado.web for use in zmq.web

This module should only contain minimal changes required for compatibility
with the extended functionality implemented in zmq.web.proxy

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import logging
import time

try:
    # Python 3
    import urllib.parse as urlparse
except ImportError:
    # Python 2
    import urlparse

from tornado import httpserver
from tornado import httputil
from tornado import web
from tornado import stack_context
from tornado.escape import native_str
from tornado.util import b

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop
from zmq.utils import jsonapi


#-----------------------------------------------------------------------------
# Service implementation
#-----------------------------------------------------------------------------


class ZMQHTTPRequest(httpserver.HTTPRequest):
    """A single HTTP request that receives requests and replies to a zmq proxy.

    This version MUST be used with the `ZMQApplicationProxy` class and sends
    the reply parts as a single zmq message. This is the default HTTP request
    class, but you can set it explicitly by passing the `http_request_class`
    argument::

        ZMQApplication(handlers, http_request_class=ZMQHTTPRequest)
    """

    def __init__(self, method, uri, version="HTTP/1.0", headers=None,
                 body=None, remote_ip=None, protocol=None, host=None,
                 files=None, connection=None, arguments=None,
                 idents=None, msg_id=None, stream=None):
        # ZMQWEB NOTE: This method is copied from the base class to make a
        # number of changes. We have added the arguments, ident, msg_id and
        # stream kwargs.
        self.method = method
        self.uri = uri
        self.version = version
        self.headers = headers or httputil.HTTPHeaders()
        self.body = body or ""
        # ZMQWEB NOTE: We simply copy the remote_ip, protocol and host as they
        # have been parsed by the other side.
        self.remote_ip = remote_ip
        self.protocol = protocol
        self.host = host
        self.files = files or {}
        # ZMQWEB NOTE: The connection attribute MUST not be saved in the
        # instance. This is because its precense triggers logic in the base
        # class that doesn't apply because ZeroMQ sockets are connectionless.
        self._start_time = time.time()
        self._finish_time = None

        # ZMQWEB NOTE: Attributes we have added to ZMQHTTPRequest.
        self.idents = idents
        self.msg_id = msg_id
        self.stream = stream
        self._chunks = []
        self._write_callback = None

        scheme, netloc, path, query, fragment = urlparse.urlsplit(native_str(uri))
        self.path = path
        self.query = query
        # ZMQWEB NOTE: We let the other side parse the arguments and simply
        # pass them into this class.
        self.arguments = arguments

    def _build_reply(self):
        """Create a new msg_list with idents and msg_id."""
        # Always create a copy as we use this multiple times.
        msg_list = []
        msg_list.extend(self.idents)
        msg_list.extend([b'|',self.msg_id])
        return msg_list

    def write(self, chunk, callback=None):
        # ZMQWEB NOTE: This method is overriden from the base class.
        logging.debug('Buffering chunk: %r', chunk)
        if callback is not None:
            self._write_callback = stack_context.wrap(callback)
        self._chunks.append(chunk)

    def finish(self):
        # ZMQWEB NOTE: This method is overriden from the base class to remove
        # a call to self.connection.finish() and send the reply message.
        msg_list = self._build_reply()
        msg_list.extend(self._chunks)
        self._chunks = []
        logging.debug('Sending reply: %r', msg_list)
        self._finish_time = time.time()
        self.stream.send_multipart(msg_list)
        if self._write_callback is not None:
            try:
                self._write_callback()
            except:
                logging.error('Unexpected exception in write callback', exc_info=True)
            self._write_callback = None

    def get_ssl_certificate(self):
        # ZMQWEB NOTE: This method is overriden from the base class.
        raise NotImplementedError('get_ssl_certificate is not implemented in this subclass')


class ZMQStreamingHTTPRequest(ZMQHTTPRequest):
    """A single HTTP request that receives requests from and replies to a zmq proxy.

    This version MUST be used with the `ZMQStreamingApplicationProxy` class
    and sends the reply parts as separate zmq messages. To use this version,
    pass the `http_request_class` argument::

        ZMQApplication(handlers, http_request_class=ZMQStreamingHTTPRequest)
    """

    def write(self, chunk, callback=None):
        # ZMQWEB NOTE: This method is overriden from the base class.
        msg_list = self._build_reply()
        msg_list.extend([b'DATA', chunk])
        logging.debug('Sending write: %r', msg_list)
        self.stream.send_multipart(msg_list)
        # ZMQWEB NOTE: We don't want to permanently register an on_send callback
        # with the stream, so we just call the callback immediately.
        if callback is not None:
            try:
                stack_context.wrap(callback)()
            except:
                logging.error('Unexpected exception in write callback', exc_info=True)

    def finish(self):
        # ZMQWEB NOTE: This method is overriden from the base class to remove
        # a call to self.connection.finish() and send the FINISH message.
        self._finish_time = time.time()
        msg_list = self._build_reply()
        msg_list.append(b'FINISH')
        logging.debug('Sending finish: %r', msg_list)
        self.stream.send_multipart(msg_list)


class ZMQApplication(web.Application):
    """A ZeroMQ based application that serves requests for a proxy.

    This class is run in a backend process and handles requests for a
    `ZMQApplicationProxy` or `ZMQStreamingApplicationProxy` class running
    in the frontend. Which of these classes is used in the frontend will
    depend on which HTTP request class is used in your backend `ZMQApplication`.
    Here is the correlation:
    
    * `ZMQApplicationProxy` with `ZMQHTTPRequest`.
    * `ZMQStreamingApplicationProxy` with `ZMQStreamingHTTPRequest`.

    To set the HTTP request class, pass the `http_request_class` setting to
    this class::

        ZMQApplication(handlers, http_request_class=ZMQStreamingHTTPRequest)
    """

    def __init__(self, handlers=None, default_host="", transforms=None,
                 wsgi=False, **settings):
        # ZMQWEB NOTE: This method is overriden from the base class.
        # ZMQWEB NOTE: We have added new context and loop settings.
        self.context = settings.pop('context', zmq.Context.instance())
        self.loop = settings.pop('loop', IOLoop.instance())
        super(ZMQApplication,self).__init__(
            handlers=handlers, default_host=default_host,
            transforms=transforms, wsgi=wsgi, **settings
        )
        # ZMQWEB NOTE: Here we create the zmq socket and stream and setup a
        # list of urls that are bound/connected to.
        self.socket = self.context.socket(zmq.ROUTER)
        self.stream = ZMQStream(self.socket, self.loop)
        self.stream.on_recv(self._handle_request)
        self.urls = []

    def connect(self, url):
        """Connect the service to the proto://ip:port given in the url."""
        # ZMQWEB NOTE: This is a new method in this subclass.
        self.urls.append(url)
        self.socket.connect(url)

    def bind(self, url):
        """Bind the service to the proto://ip:port given in the url."""
        # ZMQWEB NOTE: This is a new method in this subclass.
        self.urls.append(url)
        self.socket.bind(url)

    def _handle_request(self, msg_list):
        # ZMQWEB NOTE: This is a new method in this subclass. This method
        # is used as the on_recv callback for self.stream.
        logging.debug('Handling request: %r', msg_list)
        try:
            request, args, kwargs = self._parse_request(msg_list)
        except Exception:
            logging.error('Unexpected request message format in ZMQApplication._handle_request.', exc_info=True)
        else:
            self.__call__(request, args, kwargs)

    def _parse_request(self, msg_list):
        # ZMQWEB NOTE: This is a new method in this subclass.
        len_msg_list = len(msg_list)
        if len_msg_list < 4:
            raise IndexError('msg_list must have length 3 or more')
        # Use | as a delimeter between identities and the content.
        i = msg_list.index(b'|')
        idents = msg_list[0:i]
        msg_id = msg_list[i+1]
        req = jsonapi.loads(msg_list[i+2])
        body = msg_list[i+3] if len_msg_list==i+4 else ""

        http_request_class = self.settings.get('http_request_class',
            ZMQHTTPRequest)
        request = http_request_class(method=req['method'], uri=req['uri'],
            version=req['version'], headers=req['headers'],
            body=body, remote_ip=req['remote_ip'], protocol=req['protocol'],
            host=req['host'], files=req['files'], arguments=req['arguments'],
            idents=idents, msg_id=msg_id, stream=self.stream
        )
        args = req['args']
        kwargs = req['kwargs']
        return request, args, kwargs

    def __call__(self, request, args, kwargs):
        """Called by HTTPServer to execute the request."""
        # ZMQWEB NOTE: This method overrides the logic in the base class.
        # This is just like web.Application.__call__ but it lacks the
        # parsing logic for args/kwargs, which are already parsed on the
        # other side and are passed as arguments.
        transforms = [t(request) for t in self.transforms]
        handler = None
        args = args
        kwargs = kwargs
        handlers = self._get_host_handlers(request)
        redirect_handler_class = self.settings.get("redirect_handler_class",
                                            web.RedirectHandler)
        if not handlers:
            handler = redirect_handler_class(
                self, request, url="http://" + self.default_host + "/")
        else:
            for spec in handlers:
                match = spec.regex.match(request.path)
                if match:
                    handler = spec.handler_class(self, request, **spec.kwargs)
                    # ZMQWEB NOTE: web.Application.__call__ has logic here to
                    # parse args and kwargs. These are already parsed for us and passed
                    # into __call__ so we just use them.
                    break
            if not handler:
                handler = web.ErrorHandler(self, request, status_code=404)

        # ZMQWEB NOTE: This code is copied from the base class, but with
        # the web module name used to specify the names.
        if self.settings.get("debug"):
            with web.RequestHandler._template_loader_lock:
                for loader in web.RequestHandler._template_loaders.values():
                    loader.reset()
            web.StaticFileHandler.reset()

        handler._execute(transforms, *args, **kwargs)
        return handler

    #---------------------------------------------------------------------------
    # Methods not used from tornado.web.Application
    #---------------------------------------------------------------------------

    def listen(self, port, address="", **kwargs):
        # ZMQWEB NOTE: This method is overriden from the base class.
        raise NotImplementedError('listen is not implmemented')
