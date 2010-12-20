"""Declare basic string types unambiguously for various Python versions.

Authors
-------
* MinRK
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

import sys

major,mior = sys.version_info[:2]
if major >= 3:
    bytes = bytes
    unicode = str
    basestring = (bytes, unicode)
    asbytes = lambda s: s.encode('utf8')
elif major == 2:
    unicode = unicode
    bytes = str
    basestring = basestring
    asbytes = str

__all__ = ['asbytes', 'bytes', 'unicode', 'basestring']
