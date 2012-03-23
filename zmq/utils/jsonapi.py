"""Priority based json library imports.

Use jsonapi.loads() and jsonapi.dumps() for guaranteed symmetry.

Priority: simplejson > jsonlib2 > json

Always serializes to bytes instead of unicode for zeromq compatibility.

jsonapi.loads/dumps provide kwarg-compatibility with stdlib json.

To override pyzmq's choice of json library, you can simply override the loads/dumps
methods, e.g.::

    import ujson
    from zmq.utils import jsonapi
    jsonapi.jsonmod = ujson
    # ujson doesn't support the `separators` kwarg we use, so force its own dumps:
    jsonapi.dumps = ujson.dumps

To select the super-fast ujson module.  Note that using a different module such
as ujson that does not support the same kwargs as stdlib json may break
compatibility with other tools that depend on this, if used in the same process.
A safer route is to just serialize your own messages yourself with your favorite
library.

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

jsonmod = None

priority = ['simplejson', 'jsonlib2', 'json']
for mod in priority:
    try:
        jsonmod = __import__(mod)
    except ImportError:
        pass
    else:
        break

def _squash_unicode(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    else:
        return s

def dumps(o, **kwargs):
    """Serialize object to JSON bytes.
    See %s.dumps for details on kwargs.
    """ % jsonmod
    
    if 'separators' not in kwargs:
        kwargs['separators'] = (',', ':')
    
    return _squash_unicode(jsonmod.dumps(o, **kwargs))

def loads(s, **kwargs):
    """Load object from JSON str.
    See %s.loads for details on kwargs.
    """ % jsonmod
    
    if str is unicode and isinstance(s, bytes):
        s = s.decode('utf8')
    return jsonmod.loads(s, **kwargs)

__all__ = ['jsonmod', 'dumps', 'loads']

