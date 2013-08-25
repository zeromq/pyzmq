"""0MQ Constants."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013 Brian E. Granger & Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from zmq.backend import constants
from zmq.utils.constant_names import (
    base_names,
    switched_sockopt_names,
    int_sockopt_names,
    int64_sockopt_names,
    bytes_sockopt_names,
    ctx_opt_names,
    msg_opt_names,
)

#-----------------------------------------------------------------------------
# Python module level constants
#-----------------------------------------------------------------------------

__all__ = [
    'int_sockopts',
    'int64_sockopts',
    'bytes_sockopts',
    'ctx_opts',
    'ctx_opt_names',
    ]

int_sockopts    = set()
int64_sockopts  = set()
bytes_sockopts  = set()
ctx_opts        = set()
msg_opts        = set()


if constants.VERSION < 30000:
    int64_sockopt_names.extend(switched_sockopt_names)
else:
    int_sockopt_names.extend(switched_sockopt_names)

def _add_constant(name, container=None):
    """add a constant to be defined
    
    optionally add it to one of the sets for use in get/setopt checkers
    """
    c = getattr(constants, name, -1)
    if c == -1:
        return
    globals()[name] = c
    __all__.append(name)
    if container is not None:
        container.add(c)
    return c
    
for name in base_names:
    _add_constant(name)

for name in int_sockopt_names:
    _add_constant(name, int_sockopts)

for name in int64_sockopt_names:
    _add_constant(name, int64_sockopts)

for name in bytes_sockopt_names:
    _add_constant(name, bytes_sockopts)

for name in ctx_opt_names:
    _add_constant(name, ctx_opts)

for name in msg_opt_names:
    _add_constant(name, msg_opts)


