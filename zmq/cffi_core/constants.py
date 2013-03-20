# coding: utf-8
"""zmq constants"""

from ._cffi import C, constant_names, zmq_version_info

names = None
pynames = []

_constants = {}

for cname in constant_names:
    pyname = cname.split('_', 1)[-1]
    pynames.append(pyname)
    _constants[pyname] = getattr(C, cname)

globals().update(_constants)

if zmq_version_info()[0] == 2:
    DONTWAIT = NOBLOCK
else:
    NOBLOCK = DONTWAIT

__all__ = pynames
