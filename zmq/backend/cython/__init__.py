"""Python bindings for core 0MQ objects."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Lesser GNU Public License (LGPL).

from . import (
    error,
    message,
    context,
    socket,
    utils,
    _poll,
    _version,
    _device,
    _proxy_steerable,
)

__all__ = []
for submod in (
    error,
    message,
    context,
    socket,
    utils,
    _poll,
    _version,
    _device,
    _proxy_steerable,
):
    __all__.extend(submod.__all__)

from .error import *  # noqa
from .message import *  # noqa
from .context import *  # noqa
from .socket import *  # noqa
from ._poll import *  # noqa
from .utils import *  # noqa
from ._proxy_steerable import *  # noqa
from ._device import *  # noqa
from ._version import *  # noqa
