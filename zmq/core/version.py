"""PyZMQ and 0MQ version functions."""

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

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from zmq.core._version import zmq_version_info

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

__version__ = '2.2.0.1'
__revision__ = ''

def pyzmq_version():
    """pyzmq_version()

    Return the version of pyzmq as a string.
    """
    if __revision__:
        return '@'.join([__version__,__revision__[:6]])
    else:
        return __version__

def pyzmq_version_info():
    """pyzmq_version_info()
    
    Return the pyzmq version as a tuple of numbers
    
    If pyzmq is a dev version, the patch-version will be `inf`.
    
    This helps comparison of version tuples in Python 3, where str-int
    comparison is no longer legal for some reason.
    """
    import re
    parts = re.findall('[0-9]+', __version__)
    parts = [ int(p) for p in parts ]
    if 'dev' in __version__:
        parts.append(float('inf'))
    return tuple(parts)


def zmq_version():
    """zmq_version()

    Return the version of ZeroMQ itself as a string.
    """
    return "%i.%i.%i" % zmq_version_info()



__all__ = ['zmq_version', 'zmq_version_info',
           'pyzmq_version','pyzmq_version_info',
           '__version__', '__revision__'
]

