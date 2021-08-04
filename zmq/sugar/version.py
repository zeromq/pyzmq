"""PyZMQ and 0MQ version functions."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from typing import Tuple, Union

from zmq.backend import zmq_version_info


VERSION_MAJOR = 22
VERSION_MINOR = 2
VERSION_PATCH = 0
VERSION_EXTRA = ""
__version__ = '%i.%i.%i' % (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

version_info: Union[Tuple[int, int, int], Tuple[int, int, int, float]] = (
    VERSION_MAJOR,
    VERSION_MINOR,
    VERSION_PATCH,
)

if VERSION_EXTRA:
    __version__ = "%s.%s" % (__version__, VERSION_EXTRA)
    version_info = (
        VERSION_MAJOR,
        VERSION_MINOR,
        VERSION_PATCH,
        float('inf'),
    )

__revision__ = ''


def pyzmq_version() -> str:
    """return the version of pyzmq as a string"""
    if __revision__:
        return '@'.join([__version__, __revision__[:6]])
    else:
        return __version__


def pyzmq_version_info() -> Union[Tuple[int, int, int], Tuple[int, int, int, float]]:
    """return the pyzmq version as a tuple of at least three numbers

    If pyzmq is a development version, `inf` will be appended after the third integer.
    """
    return version_info


def zmq_version() -> str:
    """return the version of libzmq as a string"""
    return "%i.%i.%i" % zmq_version_info()


__all__ = [
    'zmq_version',
    'zmq_version_info',
    'pyzmq_version',
    'pyzmq_version_info',
    '__version__',
    '__revision__',
]
