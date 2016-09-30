"""0MQ utils."""

#
#    Copyright (c) 2010-2011 Brian E. Granger & Min Ragan-Kelley
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

from .libzmq cimport (
    zmq_curve_keypair,
    zmq_has, const_char_ptr,
)
from zmq.error import ZMQError, _check_rc, _check_version
from zmq.utils.strtypes import unicode

def has(capability):
    """Check for zmq capability by name (e.g. 'ipc', 'curve')
    
    .. versionadded:: libzmq-4.1
    .. versionadded:: 14.1
    """
    _check_version((4,1), 'zmq.has')
    cdef bytes ccap
    if isinstance(capability, unicode):
        capability = capability.encode('utf8')
    ccap = capability
    return bool(zmq_has(ccap))

def curve_keypair():
    """generate a Z85 keypair for use with zmq.CURVE security
    
    Requires libzmq (≥ 4.0) to have been built with CURVE support.
    
    .. versionadded:: libzmq-4.0
    .. versionadded:: 14.0
    
    Returns
    -------
    (public, secret) : two bytestrings
        The public and private keypair as 40 byte z85-encoded bytestrings.
    """
    cdef int rc
    cdef char[64] public_key
    cdef char[64] secret_key
    _check_version((4,0), "curve_keypair")
    rc = zmq_curve_keypair (public_key, secret_key)
    _check_rc(rc)
    return public_key, secret_key


__all__ = ['has', 'curve_keypair']
