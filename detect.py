"""Detect zmq version"""
#
#    Copyright (c) 2011 Min Ragan-Kelley
#
#    This file is part of pyzmq, copied and adapted from h5py.
#    h5py source used under the New BSD license
#
#    h5py: <http://code.google.com/p/h5py/>
#    BSD license: <http://www.opensource.org/licenses/bsd-license.php>
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

import sys
import os.path

pjoin = os.path.join

def detect_zmq(basedir, **compiler_attrs):
    """ Compile, link & execute a test program, in empty directory basedir.
    The C compiler will be updated with any keywords given via setattr.

    Returns a dictionary containing information about the zmq installation.
    """

    from distutils import ccompiler
    import subprocess

    cc = ccompiler.new_compiler()
    for name, val in compiler_attrs.items():
        setattr(cc, name, val)

    cfile = pjoin(basedir, 'vers.c')
    efile = pjoin(basedir, 'vers')

    f = open(cfile, 'w')
    try:
        f.write(
r"""
#include <stdio.h>
#include "zmq.h"

int main(){
    unsigned int major, minor, patch;
    zmq_version(&major, &minor, &patch);
    fprintf(stdout, "vers: %d.%d.%d\n", major, minor, patch);
    return 0;
}
""")
    finally:
        f.close()

    if sys.platform == 'darwin':
        # allow for missing UB arch, since it will still work:
        preargs = ['-undefined', 'dynamic_lookup']
    else:
        preargs = None

    objs = cc.compile([cfile])
    cc.link_executable(objs, efile, extra_preargs=preargs)

    result = subprocess.Popen(efile,
             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    so, se = result.communicate()
    # for py3k:
    so = so.decode()
    se = se.decode()
    if result.returncode:
        raise IOError("Error running version detection script:\n%s\n%s" % (so,se))

    handlers = {'vers':     lambda val: tuple(int(v) for v in val.split('.'))}

    props = {}
    for line in (x for x in so.split('\n') if x):
        key, val = line.split(':')
        props[key] = handlers[key](val)

    props['options'] = compiler_attrs

    return props
