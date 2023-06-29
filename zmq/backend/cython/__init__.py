"""Python bindings for core 0MQ objects."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Lesser GNU Public License (LGPL).

from . import _device, _poll, _proxy_steerable, _zmq, context, error, socket

__all__ = []
for submod in (
    error,
    # message,
    context,
    socket,
    _poll,
    _device,
    _proxy_steerable,
    _zmq,
):
    __all__.extend(submod.__all__)

from ._device import *  # noqa
from ._poll import *  # noqa
from ._proxy_steerable import *  # noqa
from ._zmq import *  # noqa
from .context import *  # noqa
from .error import *  # noqa
from .socket import *  # noqa
