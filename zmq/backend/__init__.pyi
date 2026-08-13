from collections.abc import Sequence
from typing import Any, Final, Protocol, overload, type_check_only

from _typeshed import HasFileno
from typing_extensions import Buffer, Literal, Self

import zmq

from .select import select_backend as select_backend

__all__ = [
    'Context',
    'Socket',
    'Frame',
    'Message',
    'proxy',
    'proxy_steerable',
    'zmq_poll',
    'strerror',
    'zmq_errno',
    'has',
    'curve_keypair',
    'curve_public',
    'zmq_version_info',
    'IPC_PATH_MAX_LEN',
    'PYZMQ_DRAFT_API',
]

IPC_PATH_MAX_LEN: Final[int] = ...
PYZMQ_DRAFT_API: Final[bool] = ...

class Frame:
    more: bool
    tracker: Any

    def __init__(
        self,
        data: Any = None,
        track: bool = False,
        copy: bool | None = None,
        copy_threshold: int | None = None,
    ) -> None: ...
    def __len__(self) -> int: ...
    def __copy__(self) -> Self: ...
    def fast_copy(self) -> Self: ...

    #
    @overload
    def get(self, option: int | Literal["routing_id"]) -> int: ...
    @overload
    def get(self, option: bytes | Literal["group"]) -> str: ...
    @overload
    def get(self, option: str) -> int | str: ...

    #
    @overload
    def set(self, option: Literal["routing_id"], value: int) -> None: ...
    @overload
    def set(self, option: Literal["group"], value: str | bytes) -> None: ...
    @overload
    def set(self, option: int, value: int) -> None: ...

    #
    @property
    def buffer(self) -> memoryview: ...
    @property
    def bytes(self) -> bytes: ...

Message = Frame

class Socket:
    context: zmq.Context
    copy_threshold: int

    # specific option types
    FD: int

    def __init__(
        self,
        context: Context | None = None,
        socket_type: int = -1,
        shadow: int = 0,
        copy_threshold: int | None = None,
    ) -> None: ...

    #
    @property
    def underlying(self) -> int: ...
    @property
    def closed(self) -> bool: ...

    #
    def close(self, linger: int | None = None) -> None: ...

    #
    def set(self, option: int, optval: int | bytes) -> None: ...
    def get(self, option: int) -> int | bytes: ...

    #
    def bind(self, addr: str) -> None: ...
    def connect(self, addr: str) -> None: ...
    def unbind(self, addr: str | bytes) -> None: ...
    def disconnect(self, addr: str | bytes) -> None: ...
    def monitor(
        self,
        addr: str | bytes | None,
        events: int = zmq.EVENT_ALL,
    ) -> None: ...
    def join(self, group: str | bytes) -> None: ...
    def leave(self, group: str | bytes) -> None: ...

    #
    @overload  # data: Buffer, copy=True (default)
    def send(
        self,
        data: Buffer,
        flags: int = 0,
        copy: Literal[True] = True,
        track: bool = False,
    ) -> None: ...
    @overload  # data: Buffer, copy=False (keyword)
    def send(
        self,
        data: Buffer,
        flags: int = 0,
        *,
        copy: Literal[False],
        track: bool = False,
    ) -> zmq.MessageTracker: ...
    @overload  # data: Buffer, copy=False (positional)
    def send(
        self,
        data: Buffer,
        flags: int,
        copy: Literal[False],
        track: bool = False,
    ) -> zmq.MessageTracker: ...
    @overload  # data: Frame
    def send(
        self,
        data: Frame,
        flags: int = 0,
        copy: bool = True,
        track: bool = False,
    ) -> zmq.MessageTracker: ...

    #
    @overload  # copy=True (default)
    def recv(
        self,
        flags: int = 0,
        copy: Literal[True] = True,
        track: bool = False,
    ) -> bytes: ...
    @overload  # copy=False (keyword)
    def recv(
        self,
        flags: int = 0,
        *,
        copy: Literal[False],
        track: bool = False,
    ) -> zmq.Frame: ...
    @overload  # copy=False (positional)
    def recv(
        self,
        flags: int,
        copy: Literal[False],
        track: bool = False,
    ) -> zmq.Frame: ...
    @overload  # fallback overload (mypy bug workaround)
    def recv(
        self,
        flags: int = 0,
        copy: bool = True,
        track: bool = False,
    ) -> bytes | zmq.Frame: ...

    #
    def recv_into(
        self, buffer: Buffer, /, *, nbytes: int = 0, flags: int = 0
    ) -> int: ...

class Context:
    handle: int
    closed: bool

    def __init__(self, io_threads: int = 1, shadow: int = 0) -> None: ...

    #
    @property
    def underlying(self) -> int: ...

    #
    def term(self) -> None: ...
    def set(self, option: int, optval: int) -> None: ...
    def get(self, option: int) -> int: ...

def zmq_errno() -> int: ...
def strerror(errno: int) -> str: ...
def zmq_version_info() -> tuple[int, int, int]: ...
def has(capability: str) -> bool: ...
def curve_keypair() -> tuple[bytes, bytes]: ...
def curve_public(secret_key: str | bytes) -> bytes: ...

#
@overload
def zmq_poll(
    sockets: Sequence[tuple[Socket, int]],
    timeout: int = -1,
) -> list[tuple[Socket, int]]: ...
@overload
def zmq_poll(
    sockets: Sequence[tuple[int | HasFileno, int]],
    timeout: int = -1,
) -> list[tuple[int, int]]: ...

#
def proxy(frontend: Socket, backend: Socket, capture: Socket | None = None) -> int: ...
def proxy_steerable(
    frontend: Socket,
    backend: Socket,
    capture: Socket | None = None,
    control: Socket | None = None,
) -> int: ...

@type_check_only
class _MonitoredQueueFunction(Protocol):
    def __call__(
        self,
        /,
        in_socket: Socket,
        out_socket: Socket,
        mon_socket: Socket,
        in_prefix: Buffer = b"in",
        out_prefix: Buffer = b"out",
    ) -> int: ...

# None for the cffi backend
monitored_queue: Final[_MonitoredQueueFunction | None] = ...
