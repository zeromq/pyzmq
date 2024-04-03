# zmq

```{eval-rst}
.. automodule:: zmq
```

```{currentmodule} zmq
```

## Basic Classes

````{note}
For typing purposes, `zmq.Context` and `zmq.Socket` are Generics,
which means they will accept any Context or Socket implementation.

The base `zmq.Context()` constructor returns the type
`zmq.Context[zmq.Socket[bytes]]`.
If you are using type annotations and want to _exclude_ the async subclasses,
use the resolved types instead of the base Generics:

```python
ctx: zmq.Context[zmq.Socket[bytes]] = zmq.Context()
sock: zmq.Socket[bytes]
```

in pyzmq 26, these are available as the Type Aliases (not actual classes!):

```python
ctx: zmq.SyncContext = zmq.Context()
sock: zmq.SyncSocket
```

````

### {class}`Context`

```{eval-rst}
.. autoclass:: Context
  :members:
  :inherited-members:
  :exclude-members: sockopts, closed, __del__, __enter__, __exit__, __copy__, __deepcopy__, __delattr__, __getattr__, __setattr__,

  .. attribute:: closed

      boolean - whether the context has been terminated.
      If True, you can no longer use this Context.

```

### {class}`Socket`

```{eval-rst}
.. autoclass:: Socket
  :members:
  :inherited-members:
  :exclude-members: closed, context, getsockopt_unicode, recv_unicode, setsockopt_unicode, send_unicode, __del__, __enter__, __exit__, __copy__, __deepcopy__, __delattr__, __getattr__, __setattr__,

  .. attribute:: closed

      boolean - whether the socket has been closed.
      If True, you can no longer use this Socket.

  .. attribute:: copy_threshold

      integer - size (in bytes) below which messages
      should always be copied.
      Zero-copy support has nontrivial overhead
      due to the need to coordinate garbage collection
      with the libzmq IO thread,
      so sending small messages (typically < 10s of kB)
      with ``copy=False`` is often more expensive
      than with ``copy=True``.
      The initial default value is 65536 (64kB),
      a reasonable default based on testing.

      Defaults to :const:`zmq.COPY_THRESHOLD` on socket construction.
      Setting :const:`zmq.COPY_THRESHOLD` will define the default
      value for any subsequently created sockets.

      .. versionadded:: 17

```

### {class}`Frame`

```{eval-rst}
.. autoclass:: Frame
  :members:
  :inherited-members:

```

### {class}`MessageTracker`

```{eval-rst}
.. autoclass:: MessageTracker
  :members:
  :inherited-members:

```

## Polling

### {class}`Poller`

```{eval-rst}
.. autoclass:: Poller
  :members:
  :inherited-members:

```

```{eval-rst}
.. autofunction:: zmq.select
```

## Constants

All libzmq constants are available as top-level attributes
(`zmq.PUSH`, etc.),
as well as via enums (`zmq.SocketType.PUSH`, etc.).

```{versionchanged} 23
constants for unavailable socket types
or draft features will always be defined in pyzmq,
whether the features themselves are available or not.
```

```{versionadded} 23
Each category of zmq constant is now available as an IntEnum.
```

```{eval-rst}
.. data:: COPY_THRESHOLD

    The global default "small message" threshold for copying when `copy=False`.
    Copying has a thread-coordination cost, so zero-copy only has a benefit for sufficiently large messages.
```

```{eval-rst}
.. autoenum:: SocketType
```

```{eval-rst}
.. autoenum:: SocketOption
```

```{eval-rst}
.. autoenum:: Flag
```

```{eval-rst}
.. autoenum:: PollEvent
```

```{eval-rst}
.. autoenum:: ContextOption
```

```{eval-rst}
.. autoenum:: MessageOption
```

```{eval-rst}
.. autoenum:: Event
```

```{eval-rst}
.. autoenum:: NormMode
```

```{eval-rst}
.. autoenum:: RouterNotify
```

```{eval-rst}
.. autoenum:: ReconnectStop
```

```{eval-rst}
.. autoenum:: SecurityMechanism
```

```{eval-rst}
.. autoenum:: DeviceType
```

```{eval-rst}
.. autoenum:: Errno
```

## Exceptions

### {class}`ZMQError`

```{eval-rst}
.. autoclass:: ZMQError
  :members:
  :inherited-members:

```

### {class}`ZMQVersionError`

```{eval-rst}
.. autoclass:: ZMQVersionError
  :members:
  :inherited-members:
```

### {class}`Again`

```{eval-rst}
.. autoclass:: Again

```

### {class}`ContextTerminated`

```{eval-rst}
.. autoclass:: ContextTerminated

```

### {class}`NotDone`

```{eval-rst}
.. autoclass:: NotDone

```

### {class}`ZMQBindError`

```{eval-rst}
.. autoclass:: ZMQBindError


```

## Functions

```{eval-rst}
.. autofunction:: zmq.zmq_version
```

```{eval-rst}
.. autofunction:: zmq.pyzmq_version
```

```{eval-rst}
.. autofunction:: zmq.zmq_version_info
```

```{eval-rst}
.. autofunction:: zmq.pyzmq_version_info
```

```{eval-rst}
.. autofunction:: zmq.has
```

```{eval-rst}
.. autofunction:: zmq.device
```

```{eval-rst}
.. autofunction:: zmq.proxy
```

```{eval-rst}
.. autofunction:: zmq.proxy_steerable
```

```{eval-rst}
.. autofunction:: zmq.curve_public
```

```{eval-rst}
.. autofunction:: zmq.curve_keypair
```

```{eval-rst}
.. autofunction:: zmq.get_includes
```

```{eval-rst}
.. autofunction:: zmq.get_library_dirs
```

```{eval-rst}
.. autofunction:: zmq.strerror
```
