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

major,mior = sys.version_info[:2]
if major >= 3:
    bytes = bytes
    unicode = str
    basestring = (bytes, unicode)
    asbytes = lambda s: s if isinstance(s, bytes) else unicode(s).encode('utf8')

elif major == 2:
    unicode = unicode
    bytes = str
    basestring = basestring
    asbytes = str

# give short 'b' alias for asbytes, so that we can use fake b('stuff')
# to simulate b'stuff'
b = asbytes

__all__ = ['asbytes', 'bytes', 'unicode', 'basestring', 'b']
