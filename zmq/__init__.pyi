from typing import List

from . import backend
from . import sugar

from .error import *
from .sugar import *

# mypy doesn't like overwriting symbols with * so be explicit
# about what comes from backend, not from sugar
# see tools/backend_imports.py to generate this list
# note: `x as x` is required for re-export
# see https://github.com/python/mypy/issues/2190
from .backend import (
    IPC_PATH_MAX_LEN as IPC_PATH_MAX_LEN,
    curve_keypair as curve_keypair,
    curve_public as curve_public,
    device as device,
    has as has,
    proxy as proxy,
    proxy_steerable as proxy_steerable,
    strerror as strerror,
    zmq_errno as zmq_errno,
    zmq_poll as zmq_poll,
)

COPY_THRESHOLD: int

def get_includes() -> List[str]: ...
def get_library_dirs() -> List[str]: ...
