"""
script for generating files that involve repetitive updates for zmq constants.

Run this after updating utils/constant_names

Currently generates the following files from templates:

- libzmq.pxd
- constants.pyx
- zmq_compat.h

"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Brian E. Granger & Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import os
import sys

pjoin = os.path.join

root = os.path.abspath(pjoin(os.path.dirname(__file__), os.path.pardir))

sys.path.insert(0, pjoin(root, 'zmq', 'utils'))
from constant_names import all_names, no_prefix

ifndef_t = """#ifndef {0}
    #define {0} (-1)
#endif
"""

def cython_enums():
    """generate `enum: ZMQ_CONST` block for libzmq.pxd"""
    lines = []
    for name in all_names:
        if no_prefix(name):
            lines.append('enum: ZMQ_{0} "{0}"'.format(name))
        else:
            lines.append('enum: ZMQ_{0}'.format(name))
            
    return dict(ZMQ_ENUMS='\n    '.join(lines))

def ifndefs():
    """generate `#ifndef ZMQ_CONST` block for zmq_compat.h"""
    lines = []
    for name in all_names:
        if not no_prefix(name):
            name = 'ZMQ_%s' % name
        lines.append(ifndef_t.format(name))
    return dict(ZMQ_IFNDEFS='\n'.join(lines))

def constants_pyx():
    """generate CONST = ZMQ_CONST and __all__ for constants.pyx"""
    all_lines = []
    assign_lines = []
    for name in all_names:
        assign_lines.append('{0} = ZMQ_{0}'.format(name))
        all_lines.append('  "{0}",'.format(name))
    return dict(ASSIGNMENTS='\n'.join(assign_lines), ALL='\n'.join(all_lines))

def generate_file(fname, ns_func, dest_dir="."):
    """generate a constants file from its template"""
    with open(pjoin(root, 'buildutils', '%s.tpl' % fname), 'r') as f:
        tpl = f.read()
    out = tpl.format(**ns_func())
    with open(pjoin(dest_dir, fname), 'w') as f:
        f.write(out)

if __name__ == '__main__':
    generate_file("libzmq.pxd", cython_enums, pjoin(root, 'zmq', 'backend', 'cython'))
    generate_file("constants.pyx", constants_pyx, pjoin(root, 'zmq', 'backend', 'cython'))
    generate_file("zmq_compat.h", ifndefs, pjoin(root, 'zmq', 'utils'))
