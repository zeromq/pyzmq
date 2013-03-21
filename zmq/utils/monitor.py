# -*- coding: utf-8 -*-
"""Module holding utility and convenience functions for the event monitoring facility.
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Guido Goldstein
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import struct
import zmq

# used to determine which version of the event message API is in use
LIBZMQVERSION = zmq.zmq_version_info()[:2]


def _decode_new_msg(msg):
    """Helper to decode new style event messages.

    First frame is
      16 bit event id
      32 bit event value

    *NO padding*

    Second frame is endpoint as string
    """
    if (len(msg) != 2) or (len(msg[0]) != 6):
        raise RuntimeError("Invalid event message format!", msg)
    ret = {}
    ret['event'], ret['value'] = struct.unpack("=hi", msg[0])
    ret['endpoint'] = msg[1]
    return ret

def get_monitor_message(socket):
    """Read and decode the given raw message from the monitoring socket and return a dict.

    * THIS METHOD IS ONLY USABLE ON libzmq VERSIONS >= 3.3! *
        
    The function will do a *blocking* read on the given socket!

    The returned dict will have the following entries:
      event     : int, the event id as described in libzmq.zmq_socket_monitor
      value     : int, the event value associated with the event, see libzmq.zmq_socket_monitor
      endpoint  : string, the affected endpoint
    
    Params:
      socket: the PAIR socket the message is to read from

    Returns:
      event description as dict.
    """
    # will always return a list
    msg = socket.recv_multipart()
    if LIBZMQVERSION < (3,3):
        raise NotImplementedError("libzmq event API needs libzmq version >= 3.3, you have %s!" % zmq.zmq_version())
    # new style event API
    return _decode_new_msg(msg)
