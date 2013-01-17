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
from .constants import ENOTSUP
from .socket import Socket
from zmq.error import ZMQError

class Context(ContextBase):
    sockopt = None
    opt = None
    _instance = None
    
    def __init__(self, io_threads=1):
        super(Context, self).__init__(io_threads=io_threads)
        self.sockopt = {}
        self.opt = {}
    
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
        for opt, value in self.sockopt.items():
            try:
                s.setsockopt(opt, value)
            except ZMQError:
                # ignore ZMQErrors, which are likely for socket options
                # that do not apply to a particular socket type, e.g.
                # SUBSCRIBE for non-SUB sockets.
                pass
        return s
    
    def __setattr__(self, key, value):
        """set default sockopts as attributes"""
        
        # regular setattr only allowed for defined attributes
        for obj in [self] + self.__class__.mro():
            if key in obj.__dict__:
                self.__dict__[key] = value
                return
        
        try:
            opt = getattr(constants, key.upper())
        except AttributeError:
            raise AttributeError("No such socket option: %s" % key.upper())
        else:
            self.sockopt[opt] = value
    
    def __getattr__(self, key):
        """get default sockopts as attributes"""
        key = key.upper()
        try:
            opt = getattr(constants, key)
        except AttributeError:
            raise AttributeError("no such socket option: %s" % key)
        else:
            if opt not in self.sockopt:
                raise AttributeError(key)
            else:
                return self.sockopt[opt]
    
    def __delattr__(self, key):
        """delete default sockopts as attributes"""
        key = key.upper()
        try:
            opt = getattr(constants, key)
        except AttributeError:
            raise AttributeError("no such socket option: %s" % key)
        else:
            if opt not in self.sockopt:
                raise AttributeError(key)
            else:
                del self.sockopt[opt]

__all__ = ['Context']