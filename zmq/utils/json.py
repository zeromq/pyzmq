"""Priority based json library imports.

Authors
-------
* MinRK
* Brian Granger
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

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

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

def jsonlib_dumps(o,**kwargs):
    """This one is separate because jsonlib doesn't allow specifying separators.
    See jsonlib.dumps for details on kwargs.
    """
    
    return jsonmod.dumps(o,**kwargs)

def dumps(o, **kwargs):
    """Serialize object to JSON str.
    See %s.dumps for details on kwargs.
    """%jsonmod
    
    return jsonmod.dumps(o, separators=(',',':'),**kwargs)

def loads(s,**kwargs):
    """Load object from JSON str.
    See %s.loads for details on kwargs.
    """%jsonmod
    
    return jsonmod.loads(s,**kwargs)

if jsonmod is not None and jsonmod.__name__== 'jsonlib':
    dumps = jsonlib_dumps

__all__ = ['jsonmod', 'dumps', 'dumps']

