"""Class declarations for running 0MQ Devices in the background.

Authors
-------
* MinRK
* Brian Granger
"""

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
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from zmq.core.socket cimport Socket
from zmq.core.context cimport Context

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

cdef class Device:
    """A Threadsafe 0MQ Device.
    
    For thread safety, you do not pass Sockets to this, but rather Socket
    types::

        Device(device_type, in_socket_type, out_socket_type)

    For instance::

    dev = Device(zmq.QUEUE, zmq.XREQ, zmq.XREP)

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
        passthrough for {in|out}_socket.bind(iface), to be called in the thread
    connect_{in_out}(iface)
        passthrough for {in|out}_socket.connect(iface), to be called in the
        thread
    setsockopt_{in_out}(opt,value)
        passthrough for {in|out}_socket.setsockopt(opt, value), to be called in
        the thread
    
    Attributes
    ----------
    daemon: int
        sets whether the thread should be run as a daemon
        Default is true, because if it is false, the thread will not
        exit unless it is killed
    """
    cdef public int device_type # ZMQ Device Type.
    cdef public int in_type     # Socket type for in_socket.
    cdef public int out_type    # Socket type for out_socket.
    cdef public int daemon      # Daemon flag, see Thread.daemon.
    cdef Context context        # Context for creating sockets.
    cdef Socket in_socket       # The in_socket passed to zmq.device.
    cdef Socket out_socket      # The out_socket passed to zmq.device.
    cdef list in_binds          # List of interfaces to bind ins to.
    cdef list out_binds         # List of interfaces to bind outs to.
    cdef list in_connects       # List of interfaces to connect ins to.
    cdef list out_connects      # List of interfaces to connect outs to.
    cdef list in_sockopts       # List of tuples for in.setsockopt.
    cdef list out_sockopts      # List of tuples for out.setsockopt.
    cdef int done               # bool flag for when I'm done.

    cdef int _run(self)         # underlying run method
