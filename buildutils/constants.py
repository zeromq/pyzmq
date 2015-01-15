"""
script for generating files that involve repetitive updates for zmq constants.

Run this after updating utils/constant_names

Currently generates the following files from templates:

- constant_enums.pxi
- constants.pxi
- zmq_constants.h

"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import os
import sys

from . import info
pjoin = os.path.join

root = os.path.abspath(pjoin(os.path.dirname(__file__), os.path.pardir))

sys.path.insert(0, pjoin(root, 'zmq', 'utils'))
from constant_names import all_names, no_prefix

ifndef_t = """#ifndef {0}
    #define {0} (_PYZMQ_UNDEFINED)
#endif
"""

def cython_enums():
    """generate `enum: ZMQ_CONST` block for constant_enums.pxi"""
    lines = []
    for name in all_names:
        if no_prefix(name):
            lines.append('enum: ZMQ_{0} "{0}"'.format(name))
        else:
            lines.append('enum: ZMQ_{0}'.format(name))
            
    return dict(ZMQ_ENUMS='\n    '.join(lines))

def ifndefs():
    """generate `#ifndef ZMQ_CONST` block for zmq_constants.h"""
    lines = ['#define _PYZMQ_UNDEFINED (-9999)']
    for name in all_names:
        if not no_prefix(name):
            name = 'ZMQ_%s' % name
        lines.append(ifndef_t.format(name))
    return dict(ZMQ_IFNDEFS='\n'.join(lines))

def constants_pyx():
    """generate CONST = ZMQ_CONST and __all__ for constants.pxi"""
    all_lines = []
    assign_lines = []
    for name in all_names:
        if name == "NULL":
            # avoid conflict with NULL in Cython
            assign_lines.append("globals()['NULL'] = ZMQ_NULL")
        else:
            assign_lines.append('{0} = ZMQ_{0}'.format(name))
        all_lines.append('  "{0}",'.format(name))
    return dict(ASSIGNMENTS='\n'.join(assign_lines), ALL='\n'.join(all_lines))

def generate_file(fname, ns_func, dest_dir="."):
    """generate a constants file from its template"""
    with open(pjoin(root, 'buildutils', 'templates', '%s' % fname), 'r') as f:
        tpl = f.read()
    out = tpl.format(**ns_func())
    dest = pjoin(dest_dir, fname)
    info("generating %s from template" % dest)
    with open(dest, 'w') as f:
        f.write(out)

def render_constants():
    """render generated constant files from templates"""
    generate_file("constant_enums.pxi", cython_enums, pjoin(root, 'zmq', 'backend', 'cython'))
    generate_file("constants.pxi", constants_pyx, pjoin(root, 'zmq', 'backend', 'cython'))
    generate_file("zmq_constants.h", ifndefs, pjoin(root, 'zmq', 'utils'))

if __name__ == '__main__':
    render_constants()
