"""Declare basic string types unambiguously for various Python versions.

Authors
-------
* MinRK
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2010-2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys

if sys.version_info[0] >= 3:
    bytes = bytes
    unicode = str
    basestring = (bytes, unicode)
else:
    unicode = unicode
    bytes = str
    basestring = basestring

def cast_bytes(s, encoding='utf8'):
    """cast unicode or bytes to bytes"""
    if isinstance(s, bytes):
        return s
    elif isinstance(s, unicode):
        return s.encode(encoding)
    else:
        raise TypeError("Expected unicode or bytes, got %r" % s)

def cast_unicode(s, encoding='utf8'):
    """cast bytes or unicode to unicode"""
    if isinstance(s, bytes):
        return s.decode(encoding)
    elif isinstance(s, unicode):
        return s
    else:
        raise TypeError("Expected unicode or bytes, got %r" % s)

# give short 'b' alias for cast_bytes, so that we can use fake b('stuff')
# to simulate b'stuff'
b = asbytes = cast_bytes
u = cast_unicode

__all__ = ['asbytes', 'bytes', 'unicode', 'basestring', 'b', 'u', 'cast_bytes', 'cast_unicode']
