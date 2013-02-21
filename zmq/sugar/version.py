"""PyZMQ and 0MQ version functions."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import re

from .backend import zmq_version_info

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

__version__ = '13.0.0'
__revision__ = ''

def pyzmq_version():
    """return the version of pyzmq as a string"""
    if __revision__:
        return '@'.join([__version__,__revision__[:6]])
    else:
        return __version__

def pyzmq_version_info():
    """return the pyzmq version as a tuple of numbers
    
    If pyzmq is a dev version, the patch-version will be `inf`.
    
    This helps comparison of version tuples in Python 3, where str-int
    comparison is no longer legal for some reason.
    """
    parts = re.findall('[0-9]+', __version__)
    parts = [ int(p) for p in parts ]
    if 'dev' in __version__:
        parts.append(float('inf'))
    return tuple(parts)


def zmq_version():
    """return the version of libzmq as a string"""
    return "%i.%i.%i" % zmq_version_info()


__all__ = ['zmq_version', 'zmq_version_info',
           'pyzmq_version','pyzmq_version_info',
           '__version__', '__revision__'
]

