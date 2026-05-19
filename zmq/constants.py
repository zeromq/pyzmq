"""zmq constants as enums"""

from __future__ import annotations

import errno
import sys
from enum import Enum, IntEnum, IntFlag
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

_HAUSNUMERO = 156384712


class Errno(IntEnum):
    """libzmq error codes

    .. versionadded:: 23
    """

    EAGAIN = errno.EAGAIN
    EFAULT = errno.EFAULT
    EINVAL = errno.EINVAL

    if sys.platform.startswith("win"):
        # Windows: libzmq uses errno.h
        # while Python errno prefers WSA* variants
        # many of these were introduced to errno.h in vs2010
        # ref: https://github.com/python/cpython/blob/3.9/Modules/errnomodule.c#L10-L37
        # source: https://docs.microsoft.com/en-us/cpp/c-runtime-library/errno-constants
        ENOTSUP = 129
        EPROTONOSUPPORT = 135
        ENOBUFS = 119
        ENETDOWN = 116
        EADDRINUSE = 100
        EADDRNOTAVAIL = 101
        ECONNREFUSED = 107
        EINPROGRESS = 112
        ENOTSOCK = 128
        EMSGSIZE = 115
        EAFNOSUPPORT = 102
        ENETUNREACH = 118
        ECONNABORTED = 106
        ECONNRESET = 108
        ENOTCONN = 126
        ETIMEDOUT = 138
        EHOSTUNREACH = 110
        ENETRESET = 117

    else:
        ENOTSUP = getattr(errno, "ENOTSUP", _HAUSNUMERO + 1)
        EPROTONOSUPPORT = getattr(errno, "EPROTONOSUPPORT", _HAUSNUMERO + 2)
        ENOBUFS = getattr(errno, "ENOBUFS", _HAUSNUMERO + 3)
        ENETDOWN = getattr(errno, "ENETDOWN", _HAUSNUMERO + 4)
        EADDRINUSE = getattr(errno, "EADDRINUSE", _HAUSNUMERO + 5)
        EADDRNOTAVAIL = getattr(errno, "EADDRNOTAVAIL", _HAUSNUMERO + 6)
        ECONNREFUSED = getattr(errno, "ECONNREFUSED", _HAUSNUMERO + 7)
        EINPROGRESS = getattr(errno, "EINPROGRESS", _HAUSNUMERO + 8)
        ENOTSOCK = getattr(errno, "ENOTSOCK", _HAUSNUMERO + 9)
        EMSGSIZE = getattr(errno, "EMSGSIZE", _HAUSNUMERO + 10)
        EAFNOSUPPORT = getattr(errno, "EAFNOSUPPORT", _HAUSNUMERO + 11)
        ENETUNREACH = getattr(errno, "ENETUNREACH", _HAUSNUMERO + 12)
        ECONNABORTED = getattr(errno, "ECONNABORTED", _HAUSNUMERO + 13)
        ECONNRESET = getattr(errno, "ECONNRESET", _HAUSNUMERO + 14)
        ENOTCONN = getattr(errno, "ENOTCONN", _HAUSNUMERO + 15)
        ETIMEDOUT = getattr(errno, "ETIMEDOUT", _HAUSNUMERO + 16)
        EHOSTUNREACH = getattr(errno, "EHOSTUNREACH", _HAUSNUMERO + 17)
        ENETRESET = getattr(errno, "ENETRESET", _HAUSNUMERO + 18)

    # Native 0MQ error codes
    EFSM = _HAUSNUMERO + 51
    ENOCOMPATPROTO = _HAUSNUMERO + 52
    ETERM = _HAUSNUMERO + 53
    EMTHREAD = _HAUSNUMERO + 54


class ContextOption(IntEnum):
    """Options for Context.get/set

    .. versionadded:: 23
    """

    IO_THREADS = 1
    MAX_SOCKETS = 2
    SOCKET_LIMIT = 3
    THREAD_PRIORITY = 3
    THREAD_SCHED_POLICY = 4
    MAX_MSGSZ = 5
    MSG_T_SIZE = 6
    THREAD_AFFINITY_CPU_ADD = 7
    THREAD_AFFINITY_CPU_REMOVE = 8
    THREAD_NAME_PREFIX = 9


class SocketType(IntEnum):
    """zmq socket types

    .. versionadded:: 23
    """

    PAIR = 0
    PUB = 1
    SUB = 2
    REQ = 3
    REP = 4
    DEALER = 5
    ROUTER = 6
    PULL = 7
    PUSH = 8
    XPUB = 9
    XSUB = 10
    STREAM = 11

    # deprecated aliases
    XREQ = DEALER
    XREP = ROUTER

    # DRAFT socket types
    SERVER = 12
    CLIENT = 13
    RADIO = 14
    DISH = 15
    GATHER = 16
    SCATTER = 17
    DGRAM = 18
    PEER = 19
    CHANNEL = 20


class _OptType(Enum):
    int = 'int'
    int64 = 'int64'
    bytes = 'bytes'
    fd = 'fd'


class SocketOption(IntEnum):
    """Options for Socket.get/set

    .. versionadded:: 23
    """

    _opt_type: _OptType

    def __new__(cls, value: int, opt_type: _OptType = _OptType.int) -> Self:
        """Attach option type as `._opt_type`"""
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj._opt_type = opt_type
        return obj

    HWM = 1
    AFFINITY = 4, _OptType.int64
    ROUTING_ID = 5, _OptType.bytes
    SUBSCRIBE = 6, _OptType.bytes
    UNSUBSCRIBE = 7, _OptType.bytes
    RATE = 8
    RECOVERY_IVL = 9
    SNDBUF = 11
    RCVBUF = 12
    RCVMORE = 13
    FD = 14, _OptType.fd
    EVENTS = 15
    TYPE = 16
    LINGER = 17
    RECONNECT_IVL = 18
    BACKLOG = 19
    RECONNECT_IVL_MAX = 21
    MAXMSGSIZE = 22, _OptType.int64
    SNDHWM = 23
    RCVHWM = 24
    MULTICAST_HOPS = 25
    RCVTIMEO = 27
    SNDTIMEO = 28
    LAST_ENDPOINT = 32, _OptType.bytes
    ROUTER_MANDATORY = 33
    TCP_KEEPALIVE = 34
    TCP_KEEPALIVE_CNT = 35
    TCP_KEEPALIVE_IDLE = 36
    TCP_KEEPALIVE_INTVL = 37
    IMMEDIATE = 39
    XPUB_VERBOSE = 40
    ROUTER_RAW = 41
    IPV6 = 42
    MECHANISM = 43
    PLAIN_SERVER = 44
    PLAIN_USERNAME = 45, _OptType.bytes
    PLAIN_PASSWORD = 46, _OptType.bytes
    CURVE_SERVER = 47
    CURVE_PUBLICKEY = 48, _OptType.bytes
    CURVE_SECRETKEY = 49, _OptType.bytes
    CURVE_SERVERKEY = 50, _OptType.bytes
    PROBE_ROUTER = 51
    REQ_CORRELATE = 52
    REQ_RELAXED = 53
    CONFLATE = 54
    ZAP_DOMAIN = 55, _OptType.bytes
    ROUTER_HANDOVER = 56
    TOS = 57
    CONNECT_ROUTING_ID = 61, _OptType.bytes
    GSSAPI_SERVER = 62
    GSSAPI_PRINCIPAL = 63, _OptType.bytes
    GSSAPI_SERVICE_PRINCIPAL = 64, _OptType.bytes
    GSSAPI_PLAINTEXT = 65
    HANDSHAKE_IVL = 66
    SOCKS_PROXY = 68, _OptType.bytes
    XPUB_NODROP = 69
    BLOCKY = 70
    XPUB_MANUAL = 71
    XPUB_WELCOME_MSG = 72, _OptType.bytes
    STREAM_NOTIFY = 73
    INVERT_MATCHING = 74
    HEARTBEAT_IVL = 75
    HEARTBEAT_TTL = 76
    HEARTBEAT_TIMEOUT = 77
    XPUB_VERBOSER = 78
    CONNECT_TIMEOUT = 79
    TCP_MAXRT = 80
    THREAD_SAFE = 81
    MULTICAST_MAXTPDU = 84
    VMCI_BUFFER_SIZE = 85, _OptType.int64
    VMCI_BUFFER_MIN_SIZE = 86, _OptType.int64
    VMCI_BUFFER_MAX_SIZE = 87, _OptType.int64
    VMCI_CONNECT_TIMEOUT = 88
    USE_FD = 89
    GSSAPI_PRINCIPAL_NAMETYPE = 90
    GSSAPI_SERVICE_PRINCIPAL_NAMETYPE = 91
    BINDTODEVICE = 92, _OptType.bytes

    # Deprecated options and aliases
    # must not use name-assignment, must have the same value
    IDENTITY = ROUTING_ID
    CONNECT_RID = CONNECT_ROUTING_ID
    TCP_ACCEPT_FILTER = 38, _OptType.bytes
    IPC_FILTER_PID = 58
    IPC_FILTER_UID = 59
    IPC_FILTER_GID = 60
    IPV4ONLY = 31
    DELAY_ATTACH_ON_CONNECT = IMMEDIATE
    FAIL_UNROUTABLE = ROUTER_MANDATORY
    ROUTER_BEHAVIOR = ROUTER_MANDATORY

    # Draft socket options
    ZAP_ENFORCE_DOMAIN = 93
    LOOPBACK_FASTPATH = 94
    METADATA = 95, _OptType.bytes
    MULTICAST_LOOP = 96
    ROUTER_NOTIFY = 97
    XPUB_MANUAL_LAST_VALUE = 98
    SOCKS_USERNAME = 99, _OptType.bytes
    SOCKS_PASSWORD = 100, _OptType.bytes
    IN_BATCH_SIZE = 101
    OUT_BATCH_SIZE = 102
    WSS_KEY_PEM = 103, _OptType.bytes
    WSS_CERT_PEM = 104, _OptType.bytes
    WSS_TRUST_PEM = 105, _OptType.bytes
    WSS_HOSTNAME = 106, _OptType.bytes
    WSS_TRUST_SYSTEM = 107
    ONLY_FIRST_SUBSCRIBE = 108
    RECONNECT_STOP = 109
    HELLO_MSG = 110, _OptType.bytes
    DISCONNECT_MSG = 111, _OptType.bytes
    PRIORITY = 112
    # 4.3.5
    BUSY_POLL = 113
    HICCUP_MSG = 114, _OptType.bytes
    XSUB_VERBOSE_UNSUBSCRIBE = 115
    TOPICS_COUNT = 116
    NORM_MODE = 117
    NORM_UNICAST_NACK = 118
    NORM_BUFFER_SIZE = 119
    NORM_SEGMENT_SIZE = 120
    NORM_BLOCK_SIZE = 121
    NORM_NUM_PARITY = 122
    NORM_NUM_AUTOPARITY = 123
    NORM_PUSH = 124


class MessageOption(IntEnum):
    """Options on zmq.Frame objects

    .. versionadded:: 23
    """

    MORE = 1
    SHARED = 3
    # Deprecated message options
    SRCFD = 2


class Flag(IntFlag):
    """Send/recv flags

    .. versionadded:: 23
    """

    DONTWAIT = 1
    SNDMORE = 2
    NOBLOCK = DONTWAIT


class RouterNotify(IntEnum):
    """Values for zmq.ROUTER_NOTIFY socket option

    .. versionadded:: 26
    .. versionadded:: libzmq-4.3.0 (draft)
    """

    @staticmethod
    def _global_name(name):
        return f"NOTIFY_{name}"

    CONNECT = 1
    DISCONNECT = 2


class NormMode(IntEnum):
    """Values for zmq.NORM_MODE socket option

    .. versionadded:: 26
    .. versionadded:: libzmq-4.3.5 (draft)
    """

    @staticmethod
    def _global_name(name):
        return f"NORM_{name}"

    FIXED = 0
    CC = 1
    CCL = 2
    CCE = 3
    CCE_ECNONLY = 4


class SecurityMechanism(IntEnum):
    """Security mechanisms (as returned by ``socket.get(zmq.MECHANISM)``)

    .. versionadded:: 23
    """

    NULL = 0
    PLAIN = 1
    CURVE = 2
    GSSAPI = 3


class ReconnectStop(IntEnum):
    """Select behavior for socket.reconnect_stop

    .. versionadded:: 25
    """

    @staticmethod
    def _global_name(name):
        return f"RECONNECT_STOP_{name}"

    CONN_REFUSED = 0x1
    HANDSHAKE_FAILED = 0x2
    AFTER_DISCONNECT = 0x4


class Event(IntFlag):
    """Socket monitoring events

    .. versionadded:: 23
    """

    @staticmethod
    def _global_name(name):
        if name.startswith("PROTOCOL_ERROR_"):
            return name
        else:
            # add EVENT_ prefix
            return "EVENT_" + name

    PROTOCOL_ERROR_WS_UNSPECIFIED = 0x30000000
    PROTOCOL_ERROR_ZMTP_UNSPECIFIED = 0x10000000
    PROTOCOL_ERROR_ZMTP_UNEXPECTED_COMMAND = 0x10000001
    PROTOCOL_ERROR_ZMTP_INVALID_SEQUENCE = 0x10000002
    PROTOCOL_ERROR_ZMTP_KEY_EXCHANGE = 0x10000003
    PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_UNSPECIFIED = 0x10000011
    PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_MESSAGE = 0x10000012
    PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_HELLO = 0x10000013
    PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_INITIATE = 0x10000014
    PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_ERROR = 0x10000015
    PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_READY = 0x10000016
    PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_WELCOME = 0x10000017
    PROTOCOL_ERROR_ZMTP_INVALID_METADATA = 0x10000018

    PROTOCOL_ERROR_ZMTP_CRYPTOGRAPHIC = 0x11000001
    PROTOCOL_ERROR_ZMTP_MECHANISM_MISMATCH = 0x11000002
    PROTOCOL_ERROR_ZAP_UNSPECIFIED = 0x20000000
    PROTOCOL_ERROR_ZAP_MALFORMED_REPLY = 0x20000001
    PROTOCOL_ERROR_ZAP_BAD_REQUEST_ID = 0x20000002
    PROTOCOL_ERROR_ZAP_BAD_VERSION = 0x20000003
    PROTOCOL_ERROR_ZAP_INVALID_STATUS_CODE = 0x20000004
    PROTOCOL_ERROR_ZAP_INVALID_METADATA = 0x20000005

    # define event types _after_ overlapping protocol error masks
    CONNECTED = 0x0001
    CONNECT_DELAYED = 0x0002
    CONNECT_RETRIED = 0x0004
    LISTENING = 0x0008
    BIND_FAILED = 0x0010
    ACCEPTED = 0x0020
    ACCEPT_FAILED = 0x0040
    CLOSED = 0x0080
    CLOSE_FAILED = 0x0100
    DISCONNECTED = 0x0200
    MONITOR_STOPPED = 0x0400

    HANDSHAKE_FAILED_NO_DETAIL = 0x0800
    HANDSHAKE_SUCCEEDED = 0x1000
    HANDSHAKE_FAILED_PROTOCOL = 0x2000
    HANDSHAKE_FAILED_AUTH = 0x4000

    ALL_V1 = 0xFFFF
    ALL = ALL_V1

    # DRAFT Socket monitoring events
    PIPES_STATS = 0x10000
    ALL_V2 = ALL_V1 | PIPES_STATS


class PollEvent(IntFlag):
    """Which events to poll for in poll methods

    .. versionadded: 23
    """

    POLLIN = 1
    POLLOUT = 2
    POLLERR = 4
    POLLPRI = 8


class DeviceType(IntEnum):
    """Device type constants for zmq.device

    .. versionadded: 23
    """

    STREAMER = 1
    FORWARDER = 2
    QUEUE = 3


# AUTOGENERATED_BELOW_HERE


IO_THREADS: ContextOption = ContextOption.IO_THREADS
MAX_SOCKETS: ContextOption = ContextOption.MAX_SOCKETS
SOCKET_LIMIT: ContextOption = ContextOption.SOCKET_LIMIT
THREAD_PRIORITY: ContextOption = ContextOption.THREAD_PRIORITY
THREAD_SCHED_POLICY: ContextOption = ContextOption.THREAD_SCHED_POLICY
MAX_MSGSZ: ContextOption = ContextOption.MAX_MSGSZ
MSG_T_SIZE: ContextOption = ContextOption.MSG_T_SIZE
THREAD_AFFINITY_CPU_ADD: ContextOption = ContextOption.THREAD_AFFINITY_CPU_ADD
THREAD_AFFINITY_CPU_REMOVE: ContextOption = ContextOption.THREAD_AFFINITY_CPU_REMOVE
THREAD_NAME_PREFIX: ContextOption = ContextOption.THREAD_NAME_PREFIX
STREAMER: DeviceType = DeviceType.STREAMER
FORWARDER: DeviceType = DeviceType.FORWARDER
QUEUE: DeviceType = DeviceType.QUEUE
EAGAIN: Errno = Errno.EAGAIN
EFAULT: Errno = Errno.EFAULT
EINVAL: Errno = Errno.EINVAL
ENOTSUP: Errno = Errno.ENOTSUP
EPROTONOSUPPORT: Errno = Errno.EPROTONOSUPPORT
ENOBUFS: Errno = Errno.ENOBUFS
ENETDOWN: Errno = Errno.ENETDOWN
EADDRINUSE: Errno = Errno.EADDRINUSE
EADDRNOTAVAIL: Errno = Errno.EADDRNOTAVAIL
ECONNREFUSED: Errno = Errno.ECONNREFUSED
EINPROGRESS: Errno = Errno.EINPROGRESS
ENOTSOCK: Errno = Errno.ENOTSOCK
EMSGSIZE: Errno = Errno.EMSGSIZE
EAFNOSUPPORT: Errno = Errno.EAFNOSUPPORT
ENETUNREACH: Errno = Errno.ENETUNREACH
ECONNABORTED: Errno = Errno.ECONNABORTED
ECONNRESET: Errno = Errno.ECONNRESET
ENOTCONN: Errno = Errno.ENOTCONN
ETIMEDOUT: Errno = Errno.ETIMEDOUT
EHOSTUNREACH: Errno = Errno.EHOSTUNREACH
ENETRESET: Errno = Errno.ENETRESET
EFSM: Errno = Errno.EFSM
ENOCOMPATPROTO: Errno = Errno.ENOCOMPATPROTO
ETERM: Errno = Errno.ETERM
EMTHREAD: Errno = Errno.EMTHREAD
PROTOCOL_ERROR_WS_UNSPECIFIED: Event = Event.PROTOCOL_ERROR_WS_UNSPECIFIED
PROTOCOL_ERROR_ZMTP_UNSPECIFIED: Event = Event.PROTOCOL_ERROR_ZMTP_UNSPECIFIED
PROTOCOL_ERROR_ZMTP_UNEXPECTED_COMMAND: Event = (
    Event.PROTOCOL_ERROR_ZMTP_UNEXPECTED_COMMAND
)
PROTOCOL_ERROR_ZMTP_INVALID_SEQUENCE: Event = Event.PROTOCOL_ERROR_ZMTP_INVALID_SEQUENCE
PROTOCOL_ERROR_ZMTP_KEY_EXCHANGE: Event = Event.PROTOCOL_ERROR_ZMTP_KEY_EXCHANGE
PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_UNSPECIFIED: Event = (
    Event.PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_UNSPECIFIED
)
PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_MESSAGE: Event = (
    Event.PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_MESSAGE
)
PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_HELLO: Event = (
    Event.PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_HELLO
)
PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_INITIATE: Event = (
    Event.PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_INITIATE
)
PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_ERROR: Event = (
    Event.PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_ERROR
)
PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_READY: Event = (
    Event.PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_READY
)
PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_WELCOME: Event = (
    Event.PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_WELCOME
)
PROTOCOL_ERROR_ZMTP_INVALID_METADATA: Event = Event.PROTOCOL_ERROR_ZMTP_INVALID_METADATA
PROTOCOL_ERROR_ZMTP_CRYPTOGRAPHIC: Event = Event.PROTOCOL_ERROR_ZMTP_CRYPTOGRAPHIC
PROTOCOL_ERROR_ZMTP_MECHANISM_MISMATCH: Event = (
    Event.PROTOCOL_ERROR_ZMTP_MECHANISM_MISMATCH
)
PROTOCOL_ERROR_ZAP_UNSPECIFIED: Event = Event.PROTOCOL_ERROR_ZAP_UNSPECIFIED
PROTOCOL_ERROR_ZAP_MALFORMED_REPLY: Event = Event.PROTOCOL_ERROR_ZAP_MALFORMED_REPLY
PROTOCOL_ERROR_ZAP_BAD_REQUEST_ID: Event = Event.PROTOCOL_ERROR_ZAP_BAD_REQUEST_ID
PROTOCOL_ERROR_ZAP_BAD_VERSION: Event = Event.PROTOCOL_ERROR_ZAP_BAD_VERSION
PROTOCOL_ERROR_ZAP_INVALID_STATUS_CODE: Event = (
    Event.PROTOCOL_ERROR_ZAP_INVALID_STATUS_CODE
)
PROTOCOL_ERROR_ZAP_INVALID_METADATA: Event = Event.PROTOCOL_ERROR_ZAP_INVALID_METADATA
EVENT_CONNECTED: Event = Event.CONNECTED
EVENT_CONNECT_DELAYED: Event = Event.CONNECT_DELAYED
EVENT_CONNECT_RETRIED: Event = Event.CONNECT_RETRIED
EVENT_LISTENING: Event = Event.LISTENING
EVENT_BIND_FAILED: Event = Event.BIND_FAILED
EVENT_ACCEPTED: Event = Event.ACCEPTED
EVENT_ACCEPT_FAILED: Event = Event.ACCEPT_FAILED
EVENT_CLOSED: Event = Event.CLOSED
EVENT_CLOSE_FAILED: Event = Event.CLOSE_FAILED
EVENT_DISCONNECTED: Event = Event.DISCONNECTED
EVENT_MONITOR_STOPPED: Event = Event.MONITOR_STOPPED
EVENT_HANDSHAKE_FAILED_NO_DETAIL: Event = Event.HANDSHAKE_FAILED_NO_DETAIL
EVENT_HANDSHAKE_SUCCEEDED: Event = Event.HANDSHAKE_SUCCEEDED
EVENT_HANDSHAKE_FAILED_PROTOCOL: Event = Event.HANDSHAKE_FAILED_PROTOCOL
EVENT_HANDSHAKE_FAILED_AUTH: Event = Event.HANDSHAKE_FAILED_AUTH
EVENT_ALL_V1: Event = Event.ALL_V1
EVENT_ALL: Event = Event.ALL
EVENT_PIPES_STATS: Event = Event.PIPES_STATS
EVENT_ALL_V2: Event = Event.ALL_V2
DONTWAIT: Flag = Flag.DONTWAIT
SNDMORE: Flag = Flag.SNDMORE
NOBLOCK: Flag = Flag.NOBLOCK
MORE: MessageOption = MessageOption.MORE
SHARED: MessageOption = MessageOption.SHARED
SRCFD: MessageOption = MessageOption.SRCFD
NORM_FIXED: NormMode = NormMode.FIXED
NORM_CC: NormMode = NormMode.CC
NORM_CCL: NormMode = NormMode.CCL
NORM_CCE: NormMode = NormMode.CCE
NORM_CCE_ECNONLY: NormMode = NormMode.CCE_ECNONLY
POLLIN: PollEvent = PollEvent.POLLIN
POLLOUT: PollEvent = PollEvent.POLLOUT
POLLERR: PollEvent = PollEvent.POLLERR
POLLPRI: PollEvent = PollEvent.POLLPRI
RECONNECT_STOP_CONN_REFUSED: ReconnectStop = ReconnectStop.CONN_REFUSED
RECONNECT_STOP_HANDSHAKE_FAILED: ReconnectStop = ReconnectStop.HANDSHAKE_FAILED
RECONNECT_STOP_AFTER_DISCONNECT: ReconnectStop = ReconnectStop.AFTER_DISCONNECT
NOTIFY_CONNECT: RouterNotify = RouterNotify.CONNECT
NOTIFY_DISCONNECT: RouterNotify = RouterNotify.DISCONNECT
NULL: SecurityMechanism = SecurityMechanism.NULL
PLAIN: SecurityMechanism = SecurityMechanism.PLAIN
CURVE: SecurityMechanism = SecurityMechanism.CURVE
GSSAPI: SecurityMechanism = SecurityMechanism.GSSAPI
HWM: SocketOption = SocketOption.HWM
AFFINITY: SocketOption = SocketOption.AFFINITY
ROUTING_ID: SocketOption = SocketOption.ROUTING_ID
SUBSCRIBE: SocketOption = SocketOption.SUBSCRIBE
UNSUBSCRIBE: SocketOption = SocketOption.UNSUBSCRIBE
RATE: SocketOption = SocketOption.RATE
RECOVERY_IVL: SocketOption = SocketOption.RECOVERY_IVL
SNDBUF: SocketOption = SocketOption.SNDBUF
RCVBUF: SocketOption = SocketOption.RCVBUF
RCVMORE: SocketOption = SocketOption.RCVMORE
FD: SocketOption = SocketOption.FD
EVENTS: SocketOption = SocketOption.EVENTS
TYPE: SocketOption = SocketOption.TYPE
LINGER: SocketOption = SocketOption.LINGER
RECONNECT_IVL: SocketOption = SocketOption.RECONNECT_IVL
BACKLOG: SocketOption = SocketOption.BACKLOG
RECONNECT_IVL_MAX: SocketOption = SocketOption.RECONNECT_IVL_MAX
MAXMSGSIZE: SocketOption = SocketOption.MAXMSGSIZE
SNDHWM: SocketOption = SocketOption.SNDHWM
RCVHWM: SocketOption = SocketOption.RCVHWM
MULTICAST_HOPS: SocketOption = SocketOption.MULTICAST_HOPS
RCVTIMEO: SocketOption = SocketOption.RCVTIMEO
SNDTIMEO: SocketOption = SocketOption.SNDTIMEO
LAST_ENDPOINT: SocketOption = SocketOption.LAST_ENDPOINT
ROUTER_MANDATORY: SocketOption = SocketOption.ROUTER_MANDATORY
TCP_KEEPALIVE: SocketOption = SocketOption.TCP_KEEPALIVE
TCP_KEEPALIVE_CNT: SocketOption = SocketOption.TCP_KEEPALIVE_CNT
TCP_KEEPALIVE_IDLE: SocketOption = SocketOption.TCP_KEEPALIVE_IDLE
TCP_KEEPALIVE_INTVL: SocketOption = SocketOption.TCP_KEEPALIVE_INTVL
IMMEDIATE: SocketOption = SocketOption.IMMEDIATE
XPUB_VERBOSE: SocketOption = SocketOption.XPUB_VERBOSE
ROUTER_RAW: SocketOption = SocketOption.ROUTER_RAW
IPV6: SocketOption = SocketOption.IPV6
MECHANISM: SocketOption = SocketOption.MECHANISM
PLAIN_SERVER: SocketOption = SocketOption.PLAIN_SERVER
PLAIN_USERNAME: SocketOption = SocketOption.PLAIN_USERNAME
PLAIN_PASSWORD: SocketOption = SocketOption.PLAIN_PASSWORD
CURVE_SERVER: SocketOption = SocketOption.CURVE_SERVER
CURVE_PUBLICKEY: SocketOption = SocketOption.CURVE_PUBLICKEY
CURVE_SECRETKEY: SocketOption = SocketOption.CURVE_SECRETKEY
CURVE_SERVERKEY: SocketOption = SocketOption.CURVE_SERVERKEY
PROBE_ROUTER: SocketOption = SocketOption.PROBE_ROUTER
REQ_CORRELATE: SocketOption = SocketOption.REQ_CORRELATE
REQ_RELAXED: SocketOption = SocketOption.REQ_RELAXED
CONFLATE: SocketOption = SocketOption.CONFLATE
ZAP_DOMAIN: SocketOption = SocketOption.ZAP_DOMAIN
ROUTER_HANDOVER: SocketOption = SocketOption.ROUTER_HANDOVER
TOS: SocketOption = SocketOption.TOS
CONNECT_ROUTING_ID: SocketOption = SocketOption.CONNECT_ROUTING_ID
GSSAPI_SERVER: SocketOption = SocketOption.GSSAPI_SERVER
GSSAPI_PRINCIPAL: SocketOption = SocketOption.GSSAPI_PRINCIPAL
GSSAPI_SERVICE_PRINCIPAL: SocketOption = SocketOption.GSSAPI_SERVICE_PRINCIPAL
GSSAPI_PLAINTEXT: SocketOption = SocketOption.GSSAPI_PLAINTEXT
HANDSHAKE_IVL: SocketOption = SocketOption.HANDSHAKE_IVL
SOCKS_PROXY: SocketOption = SocketOption.SOCKS_PROXY
XPUB_NODROP: SocketOption = SocketOption.XPUB_NODROP
BLOCKY: SocketOption = SocketOption.BLOCKY
XPUB_MANUAL: SocketOption = SocketOption.XPUB_MANUAL
XPUB_WELCOME_MSG: SocketOption = SocketOption.XPUB_WELCOME_MSG
STREAM_NOTIFY: SocketOption = SocketOption.STREAM_NOTIFY
INVERT_MATCHING: SocketOption = SocketOption.INVERT_MATCHING
HEARTBEAT_IVL: SocketOption = SocketOption.HEARTBEAT_IVL
HEARTBEAT_TTL: SocketOption = SocketOption.HEARTBEAT_TTL
HEARTBEAT_TIMEOUT: SocketOption = SocketOption.HEARTBEAT_TIMEOUT
XPUB_VERBOSER: SocketOption = SocketOption.XPUB_VERBOSER
CONNECT_TIMEOUT: SocketOption = SocketOption.CONNECT_TIMEOUT
TCP_MAXRT: SocketOption = SocketOption.TCP_MAXRT
THREAD_SAFE: SocketOption = SocketOption.THREAD_SAFE
MULTICAST_MAXTPDU: SocketOption = SocketOption.MULTICAST_MAXTPDU
VMCI_BUFFER_SIZE: SocketOption = SocketOption.VMCI_BUFFER_SIZE
VMCI_BUFFER_MIN_SIZE: SocketOption = SocketOption.VMCI_BUFFER_MIN_SIZE
VMCI_BUFFER_MAX_SIZE: SocketOption = SocketOption.VMCI_BUFFER_MAX_SIZE
VMCI_CONNECT_TIMEOUT: SocketOption = SocketOption.VMCI_CONNECT_TIMEOUT
USE_FD: SocketOption = SocketOption.USE_FD
GSSAPI_PRINCIPAL_NAMETYPE: SocketOption = SocketOption.GSSAPI_PRINCIPAL_NAMETYPE
GSSAPI_SERVICE_PRINCIPAL_NAMETYPE: SocketOption = (
    SocketOption.GSSAPI_SERVICE_PRINCIPAL_NAMETYPE
)
BINDTODEVICE: SocketOption = SocketOption.BINDTODEVICE
IDENTITY: SocketOption = SocketOption.IDENTITY
CONNECT_RID: SocketOption = SocketOption.CONNECT_RID
TCP_ACCEPT_FILTER: SocketOption = SocketOption.TCP_ACCEPT_FILTER
IPC_FILTER_PID: SocketOption = SocketOption.IPC_FILTER_PID
IPC_FILTER_UID: SocketOption = SocketOption.IPC_FILTER_UID
IPC_FILTER_GID: SocketOption = SocketOption.IPC_FILTER_GID
IPV4ONLY: SocketOption = SocketOption.IPV4ONLY
DELAY_ATTACH_ON_CONNECT: SocketOption = SocketOption.DELAY_ATTACH_ON_CONNECT
FAIL_UNROUTABLE: SocketOption = SocketOption.FAIL_UNROUTABLE
ROUTER_BEHAVIOR: SocketOption = SocketOption.ROUTER_BEHAVIOR
ZAP_ENFORCE_DOMAIN: SocketOption = SocketOption.ZAP_ENFORCE_DOMAIN
LOOPBACK_FASTPATH: SocketOption = SocketOption.LOOPBACK_FASTPATH
METADATA: SocketOption = SocketOption.METADATA
MULTICAST_LOOP: SocketOption = SocketOption.MULTICAST_LOOP
ROUTER_NOTIFY: SocketOption = SocketOption.ROUTER_NOTIFY
XPUB_MANUAL_LAST_VALUE: SocketOption = SocketOption.XPUB_MANUAL_LAST_VALUE
SOCKS_USERNAME: SocketOption = SocketOption.SOCKS_USERNAME
SOCKS_PASSWORD: SocketOption = SocketOption.SOCKS_PASSWORD
IN_BATCH_SIZE: SocketOption = SocketOption.IN_BATCH_SIZE
OUT_BATCH_SIZE: SocketOption = SocketOption.OUT_BATCH_SIZE
WSS_KEY_PEM: SocketOption = SocketOption.WSS_KEY_PEM
WSS_CERT_PEM: SocketOption = SocketOption.WSS_CERT_PEM
WSS_TRUST_PEM: SocketOption = SocketOption.WSS_TRUST_PEM
WSS_HOSTNAME: SocketOption = SocketOption.WSS_HOSTNAME
WSS_TRUST_SYSTEM: SocketOption = SocketOption.WSS_TRUST_SYSTEM
ONLY_FIRST_SUBSCRIBE: SocketOption = SocketOption.ONLY_FIRST_SUBSCRIBE
RECONNECT_STOP: SocketOption = SocketOption.RECONNECT_STOP
HELLO_MSG: SocketOption = SocketOption.HELLO_MSG
DISCONNECT_MSG: SocketOption = SocketOption.DISCONNECT_MSG
PRIORITY: SocketOption = SocketOption.PRIORITY
BUSY_POLL: SocketOption = SocketOption.BUSY_POLL
HICCUP_MSG: SocketOption = SocketOption.HICCUP_MSG
XSUB_VERBOSE_UNSUBSCRIBE: SocketOption = SocketOption.XSUB_VERBOSE_UNSUBSCRIBE
TOPICS_COUNT: SocketOption = SocketOption.TOPICS_COUNT
NORM_MODE: SocketOption = SocketOption.NORM_MODE
NORM_UNICAST_NACK: SocketOption = SocketOption.NORM_UNICAST_NACK
NORM_BUFFER_SIZE: SocketOption = SocketOption.NORM_BUFFER_SIZE
NORM_SEGMENT_SIZE: SocketOption = SocketOption.NORM_SEGMENT_SIZE
NORM_BLOCK_SIZE: SocketOption = SocketOption.NORM_BLOCK_SIZE
NORM_NUM_PARITY: SocketOption = SocketOption.NORM_NUM_PARITY
NORM_NUM_AUTOPARITY: SocketOption = SocketOption.NORM_NUM_AUTOPARITY
NORM_PUSH: SocketOption = SocketOption.NORM_PUSH
PAIR: SocketType = SocketType.PAIR
PUB: SocketType = SocketType.PUB
SUB: SocketType = SocketType.SUB
REQ: SocketType = SocketType.REQ
REP: SocketType = SocketType.REP
DEALER: SocketType = SocketType.DEALER
ROUTER: SocketType = SocketType.ROUTER
PULL: SocketType = SocketType.PULL
PUSH: SocketType = SocketType.PUSH
XPUB: SocketType = SocketType.XPUB
XSUB: SocketType = SocketType.XSUB
STREAM: SocketType = SocketType.STREAM
XREQ: SocketType = SocketType.XREQ
XREP: SocketType = SocketType.XREP
SERVER: SocketType = SocketType.SERVER
CLIENT: SocketType = SocketType.CLIENT
RADIO: SocketType = SocketType.RADIO
DISH: SocketType = SocketType.DISH
GATHER: SocketType = SocketType.GATHER
SCATTER: SocketType = SocketType.SCATTER
DGRAM: SocketType = SocketType.DGRAM
PEER: SocketType = SocketType.PEER
CHANNEL: SocketType = SocketType.CHANNEL

__all__: list[str] = [
    "ContextOption",
    "IO_THREADS",
    "MAX_SOCKETS",
    "SOCKET_LIMIT",
    "THREAD_PRIORITY",
    "THREAD_SCHED_POLICY",
    "MAX_MSGSZ",
    "MSG_T_SIZE",
    "THREAD_AFFINITY_CPU_ADD",
    "THREAD_AFFINITY_CPU_REMOVE",
    "THREAD_NAME_PREFIX",
    "DeviceType",
    "STREAMER",
    "FORWARDER",
    "QUEUE",
    "Enum",
    "Errno",
    "EAGAIN",
    "EFAULT",
    "EINVAL",
    "ENOTSUP",
    "EPROTONOSUPPORT",
    "ENOBUFS",
    "ENETDOWN",
    "EADDRINUSE",
    "EADDRNOTAVAIL",
    "ECONNREFUSED",
    "EINPROGRESS",
    "ENOTSOCK",
    "EMSGSIZE",
    "EAFNOSUPPORT",
    "ENETUNREACH",
    "ECONNABORTED",
    "ECONNRESET",
    "ENOTCONN",
    "ETIMEDOUT",
    "EHOSTUNREACH",
    "ENETRESET",
    "EFSM",
    "ENOCOMPATPROTO",
    "ETERM",
    "EMTHREAD",
    "Event",
    "PROTOCOL_ERROR_WS_UNSPECIFIED",
    "PROTOCOL_ERROR_ZMTP_UNSPECIFIED",
    "PROTOCOL_ERROR_ZMTP_UNEXPECTED_COMMAND",
    "PROTOCOL_ERROR_ZMTP_INVALID_SEQUENCE",
    "PROTOCOL_ERROR_ZMTP_KEY_EXCHANGE",
    "PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_UNSPECIFIED",
    "PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_MESSAGE",
    "PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_HELLO",
    "PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_INITIATE",
    "PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_ERROR",
    "PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_READY",
    "PROTOCOL_ERROR_ZMTP_MALFORMED_COMMAND_WELCOME",
    "PROTOCOL_ERROR_ZMTP_INVALID_METADATA",
    "PROTOCOL_ERROR_ZMTP_CRYPTOGRAPHIC",
    "PROTOCOL_ERROR_ZMTP_MECHANISM_MISMATCH",
    "PROTOCOL_ERROR_ZAP_UNSPECIFIED",
    "PROTOCOL_ERROR_ZAP_MALFORMED_REPLY",
    "PROTOCOL_ERROR_ZAP_BAD_REQUEST_ID",
    "PROTOCOL_ERROR_ZAP_BAD_VERSION",
    "PROTOCOL_ERROR_ZAP_INVALID_STATUS_CODE",
    "PROTOCOL_ERROR_ZAP_INVALID_METADATA",
    "EVENT_CONNECTED",
    "EVENT_CONNECT_DELAYED",
    "EVENT_CONNECT_RETRIED",
    "EVENT_LISTENING",
    "EVENT_BIND_FAILED",
    "EVENT_ACCEPTED",
    "EVENT_ACCEPT_FAILED",
    "EVENT_CLOSED",
    "EVENT_CLOSE_FAILED",
    "EVENT_DISCONNECTED",
    "EVENT_MONITOR_STOPPED",
    "EVENT_HANDSHAKE_FAILED_NO_DETAIL",
    "EVENT_HANDSHAKE_SUCCEEDED",
    "EVENT_HANDSHAKE_FAILED_PROTOCOL",
    "EVENT_HANDSHAKE_FAILED_AUTH",
    "EVENT_ALL_V1",
    "EVENT_ALL",
    "EVENT_PIPES_STATS",
    "EVENT_ALL_V2",
    "Flag",
    "DONTWAIT",
    "SNDMORE",
    "NOBLOCK",
    "IntEnum",
    "IntFlag",
    "MessageOption",
    "MORE",
    "SHARED",
    "SRCFD",
    "NormMode",
    "NORM_FIXED",
    "NORM_CC",
    "NORM_CCL",
    "NORM_CCE",
    "NORM_CCE_ECNONLY",
    "PollEvent",
    "POLLIN",
    "POLLOUT",
    "POLLERR",
    "POLLPRI",
    "ReconnectStop",
    "RECONNECT_STOP_CONN_REFUSED",
    "RECONNECT_STOP_HANDSHAKE_FAILED",
    "RECONNECT_STOP_AFTER_DISCONNECT",
    "RouterNotify",
    "NOTIFY_CONNECT",
    "NOTIFY_DISCONNECT",
    "SecurityMechanism",
    "NULL",
    "PLAIN",
    "CURVE",
    "GSSAPI",
    "SocketOption",
    "HWM",
    "AFFINITY",
    "ROUTING_ID",
    "SUBSCRIBE",
    "UNSUBSCRIBE",
    "RATE",
    "RECOVERY_IVL",
    "SNDBUF",
    "RCVBUF",
    "RCVMORE",
    "FD",
    "EVENTS",
    "TYPE",
    "LINGER",
    "RECONNECT_IVL",
    "BACKLOG",
    "RECONNECT_IVL_MAX",
    "MAXMSGSIZE",
    "SNDHWM",
    "RCVHWM",
    "MULTICAST_HOPS",
    "RCVTIMEO",
    "SNDTIMEO",
    "LAST_ENDPOINT",
    "ROUTER_MANDATORY",
    "TCP_KEEPALIVE",
    "TCP_KEEPALIVE_CNT",
    "TCP_KEEPALIVE_IDLE",
    "TCP_KEEPALIVE_INTVL",
    "IMMEDIATE",
    "XPUB_VERBOSE",
    "ROUTER_RAW",
    "IPV6",
    "MECHANISM",
    "PLAIN_SERVER",
    "PLAIN_USERNAME",
    "PLAIN_PASSWORD",
    "CURVE_SERVER",
    "CURVE_PUBLICKEY",
    "CURVE_SECRETKEY",
    "CURVE_SERVERKEY",
    "PROBE_ROUTER",
    "REQ_CORRELATE",
    "REQ_RELAXED",
    "CONFLATE",
    "ZAP_DOMAIN",
    "ROUTER_HANDOVER",
    "TOS",
    "CONNECT_ROUTING_ID",
    "GSSAPI_SERVER",
    "GSSAPI_PRINCIPAL",
    "GSSAPI_SERVICE_PRINCIPAL",
    "GSSAPI_PLAINTEXT",
    "HANDSHAKE_IVL",
    "SOCKS_PROXY",
    "XPUB_NODROP",
    "BLOCKY",
    "XPUB_MANUAL",
    "XPUB_WELCOME_MSG",
    "STREAM_NOTIFY",
    "INVERT_MATCHING",
    "HEARTBEAT_IVL",
    "HEARTBEAT_TTL",
    "HEARTBEAT_TIMEOUT",
    "XPUB_VERBOSER",
    "CONNECT_TIMEOUT",
    "TCP_MAXRT",
    "THREAD_SAFE",
    "MULTICAST_MAXTPDU",
    "VMCI_BUFFER_SIZE",
    "VMCI_BUFFER_MIN_SIZE",
    "VMCI_BUFFER_MAX_SIZE",
    "VMCI_CONNECT_TIMEOUT",
    "USE_FD",
    "GSSAPI_PRINCIPAL_NAMETYPE",
    "GSSAPI_SERVICE_PRINCIPAL_NAMETYPE",
    "BINDTODEVICE",
    "IDENTITY",
    "CONNECT_RID",
    "TCP_ACCEPT_FILTER",
    "IPC_FILTER_PID",
    "IPC_FILTER_UID",
    "IPC_FILTER_GID",
    "IPV4ONLY",
    "DELAY_ATTACH_ON_CONNECT",
    "FAIL_UNROUTABLE",
    "ROUTER_BEHAVIOR",
    "ZAP_ENFORCE_DOMAIN",
    "LOOPBACK_FASTPATH",
    "METADATA",
    "MULTICAST_LOOP",
    "ROUTER_NOTIFY",
    "XPUB_MANUAL_LAST_VALUE",
    "SOCKS_USERNAME",
    "SOCKS_PASSWORD",
    "IN_BATCH_SIZE",
    "OUT_BATCH_SIZE",
    "WSS_KEY_PEM",
    "WSS_CERT_PEM",
    "WSS_TRUST_PEM",
    "WSS_HOSTNAME",
    "WSS_TRUST_SYSTEM",
    "ONLY_FIRST_SUBSCRIBE",
    "RECONNECT_STOP",
    "HELLO_MSG",
    "DISCONNECT_MSG",
    "PRIORITY",
    "BUSY_POLL",
    "HICCUP_MSG",
    "XSUB_VERBOSE_UNSUBSCRIBE",
    "TOPICS_COUNT",
    "NORM_MODE",
    "NORM_UNICAST_NACK",
    "NORM_BUFFER_SIZE",
    "NORM_SEGMENT_SIZE",
    "NORM_BLOCK_SIZE",
    "NORM_NUM_PARITY",
    "NORM_NUM_AUTOPARITY",
    "NORM_PUSH",
    "SocketType",
    "PAIR",
    "PUB",
    "SUB",
    "REQ",
    "REP",
    "DEALER",
    "ROUTER",
    "PULL",
    "PUSH",
    "XPUB",
    "XSUB",
    "STREAM",
    "XREQ",
    "XREP",
    "SERVER",
    "CLIENT",
    "RADIO",
    "DISH",
    "GATHER",
    "SCATTER",
    "DGRAM",
    "PEER",
    "CHANNEL",
]
