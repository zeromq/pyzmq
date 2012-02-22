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

import logging
import time
import uuid
import urlparse

from tornado import httpserver
from tornado import httputil
from tornado import web
from tornado.escape import native_str

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop
from zmq.utils import jsonapi

#-----------------------------------------------------------------------------
# Service client
#-----------------------------------------------------------------------------

class ZMQApplicationProxy(object):
    """A client to a ZeroMQ based backend service."""

    def __init__(self, loop=None, context=None):
        self.loop = loop if loop is not None else IOLoop.instance()
        self.context = context if context is not None else zmq.Context.instance()
        self._callbacks = {}
        self.socket = self.context.socket(zmq.DEALER)
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

    def send_request(self, request, args, kwargs, write_callback, finish_callback):
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
        msg_list = [msg_id, jsonapi.dumps(req), body]
        self.stream.send_multipart(msg_list)
        self._callbacks[msg_id] = (write_callback, finish_callback)
        return msg_id

    def _handle_reply(self, msg_list):
        len_msg_list = len(msg_list)
        if len_msg_list < 2:
            logging.error('Unexpected reply from proxy in ZMQApplicationProxy._handle_reply')
            return
        msg_id = msg_list[0]
        reply = msg_list[1]
        cb = self._callbacks.get(msg_id)
        if cb is not None:
            write, finish = cb
            if reply == b'DATA' and len_msg_list == 3:
                try:
                    write(msg_list[2])
                except:
                    logging.error('Unexpected write error', exc_info=True)
            elif reply == b'FINISH':
                self._callbacks.pop(msg_id)
                try:
                    finish()
                except:
                    logging.error('Unexpected finish error', exc_info=True)


class ZMQRequestHandlerProxy(web.RequestHandler):
    """A handler for use with a ZeroMQ backend service client."""

    SUPPORTED_METHODS = ("GET", "HEAD", "POST", "DELETE", "PUT", "OPTIONS")

    def initialize(self, proxy):
        """Initialize with a proxy that is an instance of ZMQApplicationProxy."""
        # zmqweb Note: This method is empty in the base class.
        self.proxy = proxy

    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms."""
        # ZMQWEB NOTE: Transforms should be applied in the backend service so
        # we null any transforms passed in here. This may be a little too
        # silent, but there may be other handlers that do need the transforms.
        self._transforms = []
        # ZMQWEB NOTE: This following try/except block is taken from the base
        # class, but is modified to send the request to the proxy.
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
                # ZMQWEB NOTE: Here is where we send the request to the proxy.
                # We don't decode args or kwargs as that will be done in the
                # backen.
                self.proxy.send_request(
                    self.request, args, kwargs, self.write, self.finish
                )
        except Exception, e:
            self._handle_request_exception(e)


#-----------------------------------------------------------------------------
# Service implementation
#-----------------------------------------------------------------------------


class ZMQHTTPRequest(httpserver.HTTPRequest):
    """A single HTTP request."""

    def __init__(self, method, uri, version="HTTP/1.0", headers=None,
                 body=None, remote_ip=None, protocol=None, host=None,
                 files=None, connection=None, arguments=None,
                 ident=None, msg_id=None, stream=None):
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
        self.ident = ident
        self.msg_id = msg_id
        self.stream = stream

        scheme, netloc, path, query, fragment = urlparse.urlsplit(native_str(uri))
        self.path = path
        self.query = query
        # ZMQWEB NOTE: We let the other side parse the arguments and simply
        # pass them into this class.
        self.arguments = arguments

    def write(self, chunk, callback=None):
        # ZMQWEB NOTE: This method is overriden from the base class.
        msg_list = [self.ident, self.msg_id, b'DATA', chunk]
        self.stream.send_multipart(msg_list)
        # ZMQWEB NOTE: We don't want to permanently register an on_send callback
        # with the stream, so we just call the callback immediately.
        if callback is not None:
            try:
                callback()
            except:
                pass

    def finish(self):
        """Finishes this HTTP request on the open connection."""
        # ZMQWEB NOTE: This method is overriden from the base class to remove
        # a call to self.connection.finish() and send the FINISH message.
        self._finish_time = time.time()
        msg_list = [self.ident, self.msg_id, b'FINISH']
        self.stream.send_multipart(msg_list)

    def get_ssl_certificate(self):
        # ZMQWEB NOTE: This method is overriden from the base class.
        raise NotImplementedError('get_ssl_certificate is not implemented subclass')


class ZMQApplication(web.Application):
    """A ZeroMQ based application that serves a single handler."""

    def __init__(self, handlers=None, default_host="", transforms=None,
                 wsgi=False, **settings):
        # ZMQWEB NOTE: This method is overriden from the base class.
        # ZMQWEB NOTE: We have added new context and loop settings.
        self.context = settings.pop('context', zmq.Context.instance())
        self.loop = settings.pop('loop', IOLoop.instance())
        super(ZMQApplication,self).__init__(
            handlers=handlers, default_host=default_host,
            transforms=transforms, wsgi=wsgi, settings=settings
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
        try:
            request, args, kwargs = self._parse_request(msg_list)
        except IndexError:
            logging.error('Unexpected request message format in ZMQApplication._handle_request.')
        else:
            self.__call__(request, args, kwargs)

    def _parse_request(self, msg_list):
        # ZMQWEB NOTE: This is a new method in this subclass.
        len_msg_list = len(msg_list)
        if len_msg_list < 3:
            raise IndexError('msg_list must have length 3 or more')
        ident = msg_list[0]
        msg_id = msg_list[1]
        req = jsonapi.loads(msg_list[2])
        body = "" if len_msg_list == 3 else msg_list[3] 

        request = ZMQHTTPRequest(method=req['method'], uri=req['uri'],
            version=req['version'], headers=req['headers'],
            body=body, remote_ip=req['remote_ip'], protocol=req['protocol'],
            host=req['host'], files=req['files'], arguments=req['arguments'],
            ident=ident, msg_id=msg_id, stream=self.stream
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
        # ZMQWEB NOTE: ZMQRedirectHandler is used here.
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
                    # parse args and kwargs. This These are already parsed for us and passed
                    # into __call__ so we just use them.
                    break
            if not handler:
                handler = web.ErrorHandler(self, request, status_code=404)

        # ZMQWEB NOTE: ZMQRequestHandler and ZMQStaticFileHandler are used here.
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
