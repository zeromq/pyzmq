"""Classes for running 0MQ Devices in the background."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import time
from threading import Thread
from multiprocessing import Process

from zmq import device, QUEUE, Context, ETERM, ZMQError


class Device:
    """A 0MQ Device to be run in the background.
    
    You do not pass Socket instances to this, but rather Socket types::

        Device(device_type, in_socket_type, out_socket_type)

    For instance::

        dev = Device(zmq.QUEUE, zmq.DEALER, zmq.ROUTER)

    Similar to zmq.device, but socket types instead of sockets themselves are
    passed, and the sockets are created in the work thread, to avoid issues
    with thread safety. As a result, additional bind_{in|out} and
    connect_{in|out} methods and setsockopt_{in|out} allow users to specify
    connections for the sockets.
    
    Parameters
    ----------
    device_type : int
        The 0MQ Device type
    {in|out}_type : int
        zmq socket types, to be passed later to context.socket(). e.g.
        zmq.PUB, zmq.SUB, zmq.REQ. If out_type is < 0, then in_socket is used
        for both in_socket and out_socket.
        
    Methods
    -------
    bind_{in_out}(iface)
        passthrough for ``{in|out}_socket.bind(iface)``, to be called in the thread
    connect_{in_out}(iface)
        passthrough for ``{in|out}_socket.connect(iface)``, to be called in the
        thread
    setsockopt_{in_out}(opt,value)
        passthrough for ``{in|out}_socket.setsockopt(opt, value)``, to be called in
        the thread
    
    Attributes
    ----------
    daemon : int
        sets whether the thread should be run as a daemon
        Default is true, because if it is false, the thread will not
        exit unless it is killed
    context_factory : callable (class attribute)
        Function for creating the Context. This will be Context.instance
        in ThreadDevices, and Context in ProcessDevices.  The only reason
        it is not instance() in ProcessDevices is that there may be a stale
        Context instance already initialized, and the forked environment
        should *never* try to use it.
    """
    
    context_factory = Context.instance
    """Callable that returns a context. Typically either Context.instance or Context,
    depending on whether the device should share the global instance or not.
    """

    def __init__(self, device_type=QUEUE, in_type=None, out_type=None):
        self.device_type = device_type
        if in_type is None:
            raise TypeError("in_type must be specified")
        if out_type is None:
            raise TypeError("out_type must be specified")
        self.in_type = in_type
        self.out_type = out_type
        self._in_binds = []
        self._in_connects = []
        self._in_sockopts = []
        self._out_binds = []
        self._out_connects = []
        self._out_sockopts = []
        self.daemon = True
        self.done = False
    
    def bind_in(self, addr):
        """Enqueue ZMQ address for binding on in_socket.

        See zmq.Socket.bind for details.
        """
        self._in_binds.append(addr)
    
    def connect_in(self, addr):
        """Enqueue ZMQ address for connecting on in_socket.

        See zmq.Socket.connect for details.
        """
        self._in_connects.append(addr)
    
    def setsockopt_in(self, opt, value):
        """Enqueue setsockopt(opt, value) for in_socket

        See zmq.Socket.setsockopt for details.
        """
        self._in_sockopts.append((opt, value))
    
    def bind_out(self, addr):
        """Enqueue ZMQ address for binding on out_socket.

        See zmq.Socket.bind for details.
        """
        self._out_binds.append(addr)
    
    def connect_out(self, addr):
        """Enqueue ZMQ address for connecting on out_socket.

        See zmq.Socket.connect for details.
        """
        self._out_connects.append(addr)
    
    def setsockopt_out(self, opt, value):
        """Enqueue setsockopt(opt, value) for out_socket

        See zmq.Socket.setsockopt for details.
        """
        self._out_sockopts.append((opt, value))
    
    def _setup_sockets(self):
        ctx = self.context_factory()
        
        self._context = ctx
        
        # create the sockets
        ins = ctx.socket(self.in_type)
        if self.out_type < 0:
            outs = ins
        else:
            outs = ctx.socket(self.out_type)
        
        # set sockopts (must be done first, in case of zmq.IDENTITY)
        for opt,value in self._in_sockopts:
            ins.setsockopt(opt, value)
        for opt,value in self._out_sockopts:
            outs.setsockopt(opt, value)
        
        for iface in self._in_binds:
            ins.bind(iface)
        for iface in self._out_binds:
            outs.bind(iface)
        
        for iface in self._in_connects:
            ins.connect(iface)
        for iface in self._out_connects:
            outs.connect(iface)
        
        return ins,outs
    
    def run_device(self):
        """The runner method.

        Do not call me directly, instead call ``self.start()``, just like a Thread.
        """
        ins,outs = self._setup_sockets()
        device(self.device_type, ins, outs)
    
    def run(self):
        """wrap run_device in try/catch ETERM"""
        try:
            self.run_device()
        except ZMQError as e:
            if e.errno == ETERM:
                # silence TERM errors, because this should be a clean shutdown
                pass
            else:
                raise
        finally:
            self.done = True
    
    def start(self):
        """Start the device. Override me in subclass for other launchers."""
        return self.run()

    def join(self,timeout=None):
        """wait for me to finish, like Thread.join.
        
        Reimplemented appropriately by subclasses."""
        tic = time.time()
        toc = tic
        while not self.done and not (timeout is not None and toc-tic > timeout):
            time.sleep(.001)
            toc = time.time()


class BackgroundDevice(Device):
    """Base class for launching Devices in background processes and threads."""

    launcher=None
    _launch_class=None

    def start(self):
        self.launcher = self._launch_class(target=self.run)
        self.launcher.daemon = self.daemon
        return self.launcher.start()

    def join(self, timeout=None):
        return self.launcher.join(timeout=timeout)


class ThreadDevice(BackgroundDevice):
    """A Device that will be run in a background Thread.

    See Device for details.
    """
    _launch_class=Thread

class ProcessDevice(BackgroundDevice):
    """A Device that will be run in a background Process.

    See Device for details.
    """
    _launch_class=Process
    context_factory = Context
    """Callable that returns a context. Typically either Context.instance or Context,
    depending on whether the device should share the global instance or not.
    """


__all__ = ['Device', 'ThreadDevice', 'ProcessDevice']
