"""PyZMQ and 0MQ version functions."""

#
#    Copyright (c) 2010 Brian E. Granger
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

from czmq cimport _zmq_version

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

__version__ = '2.1.1'
__revision__ = ''

def pyzmq_version():
    """pyzmq_version()

    Return the version of pyzmq as a string.
    """
    if __revision__:
        return '@'.join([__version__,__revision__[:6]])
    else:
        return __version__


def zmq_version():
    """zmq_version()

    Return the version of ZeroMQ itself as a string.
    """
    cdef int major, minor, patch
    with nogil:
        _zmq_version(&major, &minor, &patch)
    return '%i.%i.%i' % (major, minor, patch)


__all__ = ['zmq_version', 'pyzmq_version', '__version__', '__revision__']

