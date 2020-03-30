# coding: utf-8
"""zmq constants"""

from ._cffi import ffi, lib as C
from zmq.utils.constant_names import all_names, no_prefix

c_constant_names = ['PYZMQ_DRAFT_API']
for name in all_names:
    if no_prefix(name):
        c_constant_names.append(name)
    else:
        c_constant_names.append("ZMQ_" + name)


g = globals()
for cname in c_constant_names:
    if cname.startswith("ZMQ_"):
        name = cname[4:]
    else:
        name = cname
    g[name] = getattr(C, cname)

DRAFT_API = C.PYZMQ_DRAFT_API
__all__ = ['DRAFT_API'] + all_names
