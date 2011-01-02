'''

sphinx_cython.py

This module monkeypatches sphinx autodoc to support Cython generated
function signatures in the first line of the docstring of functions
implemented as C extensions. 

Copyright (C) Nikolaus Rath <Nikolaus@rath.org>

This file is part of LLFUSE (http://python-llfuse.googlecode.com).
LLFUSE can be distributed under the terms of the GNU LGPL.

It has been slightly modified by MinRK.
'''

import sphinx.ext.autodoc as SphinxAutodoc
from sphinx.util.docstrings import prepare_docstring
import inspect
import re
from sphinx.util import force_decode

TYPE_RE = re.compile(r'(?:int|char)(?:\s+\*?\s*|\s*\*?\s+)([a-zA-Z_].*)')

ClassDocumenter  = SphinxAutodoc.ClassDocumenter
MethodDocumenter = SphinxAutodoc.MethodDocumenter
FunctionDocumenter = SphinxAutodoc.FunctionDocumenter

class MyDocumenter(SphinxAutodoc.Documenter):
    '''
    Overwrites `get_doc()` to remove function and
    method signatures and `format_args` to parse and give
    precedence to function signatures in the first line
    of the docstring. 
    ''' 

    def get_doc(self, encoding=None):
        docstr = self.get_attr(self.object, '__doc__', None)
        
        myname = self.fullname[len(self.modname)+1:]
        if myname.endswith('()'):
            myname = myname[:-2]
            
        if (docstr
            and (myname + '(') in docstr
            and '\n' in docstr
            and docstr[docstr.index('\n')-1] == ')'):
            docstr = docstr[docstr.index('\n')+1:]
                    
        if docstr:
            # make sure we have Unicode docstrings, then sanitize and split
            # into lines
            return [prepare_docstring(force_decode(docstr, encoding))]
        return []
        
        
    def format_args(self):
        myname = self.fullname[len(self.modname)+1:]
        if myname.endswith('()'):
            myname = myname[:-2]
        # Try to parse docstring
        docstr = self.get_attr(self.object, '__doc__', None)
        if (docstr 
            and (myname + '(') in docstr
            and '\n' in docstr
            and docstr[docstr.index('\n')-1] == ')'):
            args = docstr[len(myname)+1:docstr.index('\n')-1]
            
            # Get rid of Cython style types declarations
            argl = []
            for arg in [ x.strip() for x in args.split(',') ]:
                if (arg in ('cls', 'self') 
                    and isinstance(self, SphinxAutodoc.MethodDocumenter)):
                    continue 
                hit = TYPE_RE.match(arg)
                if hit:
                    argl.append(hit.group(1))
                else:
                    argl.append(arg)
            args = '(%s)' % ', '.join(argl)
        else:
            # super seems to get this wrong:
            for cls in (MethodDocumenter,
                        FunctionDocumenter,
                        ClassDocumenter):
                if isinstance(self, cls):
                    return cls.format_args(self)
            # return super(self.__class__, self).format_args()  

        # escape backslashes for reST
        args = args.replace('\\', '\\\\')
        return args


class MyFunctionDocumenter(MyDocumenter, SphinxAutodoc.FunctionDocumenter):
    pass
        
class MyMethodDocumenter(MyDocumenter, SphinxAutodoc.MethodDocumenter):    
    pass

class MyClassDocumenter(MyDocumenter, SphinxAutodoc.ClassDocumenter):    
    def format_signature(self):
        return self.format_args() or "()"

SphinxAutodoc.ClassDocumenter = MyClassDocumenter 
SphinxAutodoc.MethodDocumenter = MyMethodDocumenter 
SphinxAutodoc.FunctionDocumenter = MyFunctionDocumenter

# don't use AttributeDocumenter on 'method_descriptor' members:
AD = SphinxAutodoc.AttributeDocumenter
AD.method_types = tuple(list(AD.method_types) + [type(str.count)])
