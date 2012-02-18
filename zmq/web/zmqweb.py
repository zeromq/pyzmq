"""An architecture that allows Tornado handlers to be run in processes.

This module uses ZeroMQ/PyZMQ sockets (DEALER/ROUTER) to enable individual
Tornado handlers to be run in a separate backend service process. Through the
usage of DEALER/ROUTER sockets, multiple backend service processes for a given 
handler can be started and requests will be load balanced among the service
processes.
 
Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#
#    Copyright (c) 2012 Min Ragan-Kelley, Brian Granger
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
#
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import Cookie
import logging
import time
import uuid
import urlparse

from tornado import httpserver
from tornado import httputil
from tornado import web
from tornado.escape import native_str
from tornado.util import b

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop
from zmq.utils import jsonapi

#-----------------------------------------------------------------------------
# Service client
#-----------------------------------------------------------------------------

class ZMQWebApplicationProxy(object):
    """A client to a ZeroMQ based backend service."""

    def __init__(self, loop=None, context=None):
        self.loop = loop if loop is not None else IOLoop.instance()
        self.context = context if context is not None else zmq.Context.instance()
        self._callbacks = {}
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, bytes(uuid.uuid4()))
        self.stream = ZMQStream(self.socket, self.loop)
        self.stream.on_recv(self._handle_reply)
        self.urls = []

    def connect(self, url):
        """Connect the service client to the proto://ip:port given in the url."""
        self.urls.append(url)
        self.socket.connect(url)

    def bind(self, url):
        """Bind the service client to the proto://ip:port given in the url."""
        self.urls.append(url)
        self.socket.bind(url)

    def send_request(self, request, args, kwargs, callback=None):
        """Send a request to the service."""
        req = {}
        req['method'] = request.method
        req['uri'] = request.uri
        req['version'] = request.version
        req['headers'] = dict(request.headers)
        body = request.body
        req['remote_ip'] = request.remote_ip
        req['protocol'] = request.protocol
        req['host'] = request.host
        req['files'] = request.files
        req['arguments'] = request.arguments
        req['args'] = args
        req['kwargs'] = kwargs

        msg_id = bytes(uuid.uuid4())
        self.stream.send(msg_id, zmq.SNDMORE)
        self.stream.send(jsonapi.dumps(req), zmq.SNDMORE)
        self.stream.send(body)
        self._callbacks[msg_id] = callback
        return msg_id

    def _handle_reply(self, msg_list):
        msg_id = msg_list[0]
        header_data = jsonapi.loads(msg_list[1])
        body = msg_list[2]
        cb = self._callbacks.get(msg_id)
        if cb is not None:
            try:
                cb(header_data, body)
            except:
                logging.error('Unexpected callback error', exc_info=True)
                return


class ZMQRequestHandlerProxy(web.RequestHandler):
    """A handler for use with a ZeroMQ backend service client."""

    SUPPORTED_METHODS = ("GET", "HEAD", "POST", "DELETE", "PUT", "OPTIONS")

    def initialize(self, proxy):
        self.proxy = proxy

    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms."""
        # Transforms should be applied in the backend service so we null any
        # transforms passed in here. This may be a little too silent, but
        # there may be other handlers that do need the transforms.
        self._transforms = []
        try:
            if self.request.method not in self.SUPPORTED_METHODS:
                raise web.HTTPError(405)
            # If XSRF cookies are turned on, reject form submissions without
            # the proper cookie
            if self.request.method not in ("GET", "HEAD", "OPTIONS") and \
               self.application.settings.get("xsrf_cookies"):
                self.check_xsrf_cookie()
            self.prepare()
            if not self._finished:
                # Don't decode args or kwargs as that will be done in the backen.
                self.proxy.send_request(self.request, args, kwargs,
                    self._handle_reply)
        except Exception, e:
            self._handle_request_exception(e)

    def _handle_reply(self, header_data, body):
        # We simple save the headers and status code in the attributes
        # web.RequestHandler uses.
        self._headers = header_data['headers']
        self._status_code = header_data['status_code']
        self._list_headers = header_data['list_headers']
        # new_cookies is  a list of cookie strings each of which we must
        # wrap in a BaseCookie. We don't use SimpleCookie, because the other side has
        # already run the values through the encoding logic of SimpleCookie. 
        cookie_list = header_data['new_cookies']
        self._new_cookies = [Cookie.BaseCookie(cookie) for cookie in cookie_list]
        self.write(body)
        self.finish()


#-----------------------------------------------------------------------------
# Service implementation
#-----------------------------------------------------------------------------


class ZMQHTTPRequest(httpserver.HTTPRequest):
    """A single HTTP request."""

    def __init__(self, method, uri, version="HTTP/1.0", headers=None,
                 body=None, remote_ip=None, protocol=None, host=None,
                 files=None, connection=None, arguments=None,
                 ident=None, msg_id=None, stream=None):
        # The connection attribute MUST be missing as tornado tried to access
        # connection.stream if connection exists. None of this is needed as
        # ZeroMQ is connectionless.
        self.method = method
        self.uri = uri
        self.version = version
        self.headers = headers or httputil.HTTPHeaders()
        self.body = body or ""
        self.remote_ip = remote_ip
        self.protocol = protocol
        self.host = host
        self.files = files or {}
        self._start_time = time.time()
        self._finish_time = None
        # Attributes we have added to ZMQHTTPRequest.
        self.ident = ident
        self.msg_id = msg_id
        self.stream = stream

        scheme, netloc, path, query, fragment = urlparse.urlsplit(native_str(uri))
        self.path = path
        self.query = query
        # We let the original request and httpserver parse the arguments and simply
        # pass them into this class.
        self.arguments = arguments

    def write(self, header_data, body=None):
        """Writes the given chunk to the response stream."""
        self.stream.send(self.ident, zmq.SNDMORE)
        self.stream.send(self.msg_id, zmq.SNDMORE)
        if body is None:
            self.stream.send(header_data)
        else:
            self.stream.send(header_data, zmq.SNDMORE)
            self.stream.send(body)

    def finish(self):
        """Finishes this HTTP request on the open connection."""
        self._finish_time = time.time()

    def get_ssl_certificate(self):
        """Returns the client's SSL certificate, if any."""
        raise NotImplementedError('get_ssl_certificate is not implemented subclass')


class ZMQWebApplication(web.Application):
    """A ZeroMQ based application that serves a single handler."""

    def __init__(self, handlers=None, default_host="", transforms=None,
                 wsgi=False, **settings):
        self.context = settings.pop('context', zmq.Context.instance())
        self.loop = settings.pop('loop', IOLoop.instance())
        super(ZMQWebApplication,self).__init__(
            handlers=handlers, default_host=default_host,
            transforms=transforms, wsgi=wsgi, settings=settings
        )
        self.socket = self.context.socket(zmq.ROUTER)
        self.stream = ZMQStream(self.socket, self.loop)
        self.stream.on_recv(self._handle_request)
        self.urls = []

    def connect(self, url):
        """Connect the service to the proto://ip:port given in the url."""
        self.urls.append(url)
        self.socket.connect(url)

    def bind(self, url):
        """Bind the service to the proto://ip:port given in the url."""
        self.urls.append(url)
        self.socket.bind(url)

    def _handle_request(self, msg_list):
        request, args, kwargs = self._parse_request(msg_list)
        self.__call__(request, args, kwargs)

    def _parse_request(self, msg_list):
        # Read message parts and build the request
        ident = msg_list[0]
        msg_id = msg_list[1]
        req = jsonapi.loads(msg_list[2])

        method = req['method']
        uri = req['uri']
        version = req['version']
        headers = req['headers']
        body = msg_list[3]
        remote_ip = req['remote_ip']
        protocol = req['protocol']
        host = req['host']
        files = req['files']
        arguments = req['arguments']
        request = ZMQHTTPRequest(method=method, uri=uri, version=version,
            headers=headers, body=body, remote_ip=remote_ip, protocol=protocol,
            host=host, files=files, arguments=arguments,
            ident=ident, msg_id=msg_id, stream=self.stream)

        args = req['args']
        kwargs = req['kwargs']
        return request, args, kwargs

    def __call__(self, request, args, kwargs):
        """Called by HTTPServer to execute the request."""
        # This is just like web.Application.__call__ but it lacks the
        # parsing logic for args/kwargs. This is already done so we pass
        # them in.
        transforms = [t(request) for t in self.transforms]
        handler = None
        handlers = self._get_host_handlers(request)
        if not handlers:
            handler = RedirectHandler(
                self, request, url="http://" + self.default_host + "/")
        else:
            for spec in handlers:
                match = spec.regex.match(request.path)
                if match:
                    handler = spec.handler_class(self, request, **spec.kwargs)
                    # web.Application.__call__ has logic here to parse args
                    # and kwargs. These are already parsed for us and passed
                    # into __call__ so we just use them.
                    break
            if not handler:
                handler = ErrorHandler(self, request, status_code=404)

        # In debug mode, re-compile templates and reload static files on every
        # request so you don't need to restart to see changes
        if self.settings.get("debug"):
            with RequestHandler._template_loader_lock:
                for loader in RequestHandler._template_loaders.values():
                    loader.reset()
            StaticFileHandler.reset()

        handler._execute(transforms, *args, **kwargs)
        return handler

    #---------------------------------------------------------------------------
    # Methods not used from tornado.web.Application
    #---------------------------------------------------------------------------

    def listen(self, port, address="", **kwargs):
        raise NotImplementedError('listen is not implmemented')


class ZMQRequestHandler(web.RequestHandler):
    """A ZeroMQ based handler subclass."""

    def flush(self, include_footers=False, callback=None):
        raise NotImplementedError('flush is not supported in this handler')

    def finish(self, chunk=None):
        """Finishes this response, ending the HTTP request."""
        if self._finished:
            raise RuntimeError("finish() called twice.  May be caused "
                               "by using async operations without the "
                               "@asynchronous decorator.")

        if chunk is not None:
            self.write(chunk)

        # Automatically support ETags and add the Content-Length header if
        # we have not flushed any content yet.
        if not self._headers_written:
            if (self._status_code == 200 and
                self.request.method in ("GET", "HEAD") and
                "Etag" not in self._headers):
                etag = self.compute_etag()
                if etag is not None:
                    inm = self.request.headers.get("If-None-Match")
                    if inm and inm.find(etag) != -1:
                        self._write_buffer = []
                        self.set_status(304)
                    else:
                        self.set_header("Etag", etag)
            if "Content-Length" not in self._headers:
                content_length = sum(len(part) for part in self._write_buffer)
                self.set_header("Content-Length", content_length)

        # Logic from flush
        chunk = b("").join(self._write_buffer)
        self._write_buffer = []
        self._headers_written = True
        for transform in self._transforms:
            self._headers, chunk = transform.transform_first_chunk(
                self._headers, chunk, True)

        # self._new_cookies is a list of Cookie.SimpleCookie objects, which are
        # subclasses of dict. We use .output() to get their cookie strings
        # which are used to reconstruct the cookies on the other side. 
        if hasattr(self, '_new_cookies'):
            new_cookies = [cookie.output() for cookie in self._new_cookies]
        else:
            new_cookies = []
        header_data = {
            'headers': self._headers,
            'list_headers': self._list_headers,
            'status_code': self._status_code,
            'new_cookies': new_cookies
        }
        header_data = jsonapi.dumps(header_data)

        # Ignore the chunk and only write the headers for HEAD requests
        if self.request.method == "HEAD":
            self.request.write(header_data)
        else:
            self.request.write(header_data, chunk)

        self.request.finish()
        self._log()
        self._finished = True
        if hasattr(self,'on_finish'):
            self.on_finish()


class ZMQErrorHandler(web.ErrorHandler, ZMQRequestHandler):
    pass


class ZMQRedirectHandler(web.RedirectHandler, ZMQRequestHandler):
    pass


class ZMQStaticFileHandler(web.StaticFileHandler, ZMQRequestHandler):
    pass


class ZMQFallbackHandler(web.FallbackHandler, ZMQRequestHandler):
    pass

# Monkey patch the default handlers to use our versions. For any process that
# imports webzmq, our versions will be used.
Application = ZMQWebApplication
RequestHandler = ZMQRequestHandler
ErrorHandler= web.ErrorHandler = ZMQErrorHandler
RedirectHandler = web.RedirectHandler = ZMQRedirectHandler
StaticFileHandler = web.StaticFileHandler = ZMQStaticFileHandler
FallbackHandler = web.FallbackHandler = ZMQFallbackHandler
