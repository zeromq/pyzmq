"""Python bindings for 0MQ."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from .backend import Context as ContextBase
from . import constants
from .attrsettr import AttributeSetter
from .constants import ENOTSUP, ctx_opt_names
from .socket import Socket
from zmq.error import ZMQError

class Context(ContextBase, AttributeSetter):
    sockopts = None
    _instance = None
    
    def __init__(self, io_threads=1):
        super(Context, self).__init__(io_threads=io_threads)
        self.sockopts = {}
    
    # static method copied from tornado IOLoop.instance
    @classmethod
    def instance(cls, io_threads=1):
        """Returns a global Context instance.

        Most single-threaded applications have a single, global Context.
        Use this method instead of passing around Context instances
        throughout your code.

        A common pattern for classes that depend on Contexts is to use
        a default argument to enable programs with multiple Contexts
        but not require the argument for simpler applications:

            class MyClass(object):
                def __init__(self, context=None):
                    self.context = context or Context.instance()
        """
        if cls._instance is None or cls._instance.closed:
            cls._instance = cls(io_threads=io_threads)
        return cls._instance

    #-------------------------------------------------------------------------
    # Hooks for ctxopt completion
    #-------------------------------------------------------------------------
    
    def __dir__(self):
        keys = dir(self.__class__)

        for collection in (
            ctx_opt_names,
        ):
            keys.extend(collection)
        return keys

    #-------------------------------------------------------------------------
    # Creating Sockets
    #-------------------------------------------------------------------------

    @property
    def _socket_class(self):
        return Socket
    
    def socket(self, socket_type):
        """ctx.socket(socket_type)

        Create a Socket associated with this Context.

        Parameters
        ----------
        socket_type : int
            The socket type, which can be any of the 0MQ socket types: 
            REQ, REP, PUB, SUB, PAIR, DEALER, ROUTER, PULL, PUSH, XSUB, XPUB.
        """
        if self.closed:
            raise ZMQError(ENOTSUP)
        s = self._socket_class(self, socket_type)
        for opt, value in self.sockopts.items():
            try:
                s.setsockopt(opt, value)
            except ZMQError:
                # ignore ZMQErrors, which are likely for socket options
                # that do not apply to a particular socket type, e.g.
                # SUBSCRIBE for non-SUB sockets.
                pass
        return s
    
    def setsockopt(self, opt, value):
        """set default socket options for new sockets created by this Context"""
        self.sockopts[opt] = value
    
    def getsockopt(self, opt):
        """get default socket options for new sockets created by this Context"""
        return self.sockopts[opt]
    
    def _set_attr_opt(self, name, opt, value):
        """set default sockopts as attributes"""
        if name in constants.ctx_opt_names:
            return self.set(opt, value)
        else:
            self.sockopts[opt] = value
    
    def _get_attr_opt(self, name, opt):
        """get default sockopts as attributes"""
        if name in constants.ctx_opt_names:
            return self.get(opt)
        else:
            if opt not in self.sockopts:
                raise AttributeError(name)
            else:
                return self.sockopts[opt]
    
    def __delattr__(self, key):
        """delete default sockopts as attributes"""
        key = key.upper()
        try:
            opt = getattr(constants, key)
        except AttributeError:
            raise AttributeError("no such socket option: %s" % key)
        else:
            if opt not in self.sockopts:
                raise AttributeError(key)
            else:
                del self.sockopts[opt]

__all__ = ['Context']