# -*- coding: utf-8 -*-
"""Module holding utility and convenience functions for zmq event monitoring."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Guido Goldstein, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import struct
import zmq

# used to determine which version of the event message API is in use
LIBZMQVERSION = zmq.zmq_version_info()

def _decode_new_msg(msg):
    """decode 3.3-style event messages.

    First frame is
      16 bit event id
      32 bit event value

    *NO padding*

    Second frame is endpoint as bytestring
    """
    if len(msg) != 2 or len(msg[0]) != 6:
        raise RuntimeError("Invalid event message format: %s" % msg)
    event = {}
    event['event'], event['value'] = struct.unpack("=hi", msg[0])
    event['endpoint'] = msg[1]
    return event

def get_monitor_message(socket, flags=0):
    """Receive and decode the given raw message from the monitoring socket and return a dict.

    * THIS METHOD IS ONLY USABLE ON libzmq VERSIONS >= 3.3! *

    The returned dict will have the following entries:
      event     : int, the event id as described in libzmq.zmq_socket_monitor
      value     : int, the event value associated with the event, see libzmq.zmq_socket_monitor
      endpoint  : string, the affected endpoint
    
    Parameters
    ----------
    socket : zmq PAIR socket
        The PAIR socket (created by other_socket.connect_monitor()) on which to recv the message
    flags : bitfield (int)
        standard zmq recv flags

    Returns
    -------
    
    event : dict
        event description as dict with the keys `event`, `value`, and `endpoint`.
    """
    if LIBZMQVERSION < (4,):
        raise NotImplementedError("libzmq event API needs libzmq version >= 3.3, you have %s!" % zmq.zmq_version())
    # will always return a list
    msg = socket.recv_multipart(flags)
    # 3.3-style event API
    return _decode_new_msg(msg)
