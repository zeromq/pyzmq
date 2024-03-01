# asyncio

## Module: {mod}`zmq.asyncio`

```{eval-rst}
.. automodule:: zmq.asyncio
```

```{currentmodule} zmq.asyncio
```

```{versionadded} 15.0
```

As of 15.0, pyzmq now supports {mod}`asyncio`, via {mod}`zmq.asyncio`.
When imported from this module, blocking methods such as
{meth}`Socket.recv_multipart`, {meth}`Socket.poll`,
and {meth}`Poller.poll` return {class}`~.asyncio.Future` s.

```python
import asyncio
import zmq
import zmq.asyncio

ctx = zmq.asyncio.Context()


async def recv_and_process():
    sock = ctx.socket(zmq.PULL)
    sock.bind(url)
    msg = await sock.recv_multipart()  # waits for msg to be ready
    reply = await async_process(msg)
    await sock.send_multipart(reply)


asyncio.run(recv_and_process())
```

## Classes

### {class}`Context`

Context class that creates Future-returning sockets. See {class}`zmq.Context` for more info.

```{eval-rst}
.. autoclass:: Context


```

### {class}`Socket`

Socket subclass that returns {class}`asyncio.Future` s from blocking methods,
for use in coroutines and async applications.

```{seealso}
{class}`zmq.Socket` for the inherited API.
```

```{eval-rst}
.. autoclass:: Socket

  .. automethod:: recv

  .. automethod:: recv_multipart

  .. automethod:: send

  .. automethod:: send_multipart

  .. automethod:: poll

```

### {class}`Poller`

Poller subclass that returns {class}`asyncio.Future` s from poll,
for use in coroutines and async applications.

```{seealso}
{class}`zmq.Poller` for the inherited API.
```

```{eval-rst}
.. autoclass:: Poller

  .. automethod:: poll
```
