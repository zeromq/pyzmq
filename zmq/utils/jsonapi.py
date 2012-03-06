"""Priority based json library imports.

Use jsonapi.loads() and jsonapi.dumps() for guaranteed symmetry.

Priority: jsonlib2 > jsonlib > simplejson > json

Ensures bytes instead of unicode on either side of serialization.

Authors
-------
* MinRK
* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2010-2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from zmq.utils.strtypes import bytes, unicode
# priority: jsonlib2 > jsonlib > simplejson > json

jsonmod = None

try:
    import jsonlib2 as jsonmod
except ImportError:
    try:
        import jsonlib as jsonmod
    except ImportError:
        try:
            import simplejson as jsonmod
        except ImportError:
            try:
                import json as jsonmod
            except ImportError:
                pass

def _squash_unicode(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    else:
        return s

def jsonlib_dumps(o,**kwargs):
    """This one is separate because jsonlib doesn't allow specifying separators.
    See jsonlib.dumps for details on kwargs.
    """
    return _squash_unicode(jsonmod.dumps(o,**kwargs))

def dumps(o, **kwargs):
    """Serialize object to JSON str.
    See %s.dumps for details on kwargs.
    """%jsonmod
    
    return _squash_unicode(jsonmod.dumps(o, separators=(',',':'),**kwargs))

def loads(s,**kwargs):
    """Load object from JSON str.
    See %s.loads for details on kwargs.
    """%jsonmod
    if str is unicode and isinstance(s, bytes):
        s = s.decode('utf8')
    return jsonmod.loads(s,**kwargs)

if jsonmod is not None and jsonmod.__name__== 'jsonlib':
    dumps = jsonlib_dumps

__all__ = ['jsonmod', 'dumps', 'loads']

