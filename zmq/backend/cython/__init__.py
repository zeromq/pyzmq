"""Python bindings for core 0MQ objects."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Lesser GNU Public License (LGPL).

from . import _zmq
from ._zmq import *  # noqa

Message = _zmq.Frame

__all__ = ["Message"]
__all__.extend(_zmq.__all__)
