% PyZMQ serialization doc, by Min Ragan-Kelley, 2011

(serialization)=

# Serializing messages with PyZMQ

When sending messages over a network, you often need to marshall your data into bytes.

## Builtin serialization

PyZMQ is primarily bindings for libzmq, but we do provide some builtin serialization
methods for convenience, to help Python developers learn libzmq. Python has two primary
modules for serializing objects in the standard library: {py:mod}`json` and {py:mod}`pickle`,
so pyzmq provides simple convenience methods for sending and receiving objects serialized with these modules.
A socket has the methods {meth}`~.Socket.send_json` and
{meth}`~.Socket.send_pyobj`, which correspond to sending an object over the wire after
serializing with json and pickle respectively, and any object sent via those
methods can be reconstructed with the {meth}`~.Socket.recv_json` and
{meth}`~.Socket.recv_pyobj` methods.

```{note}
These methods are meant more for convenience and demonstration purposes, not for performance or safety.
Applications should usually define their own serialized send/recv functions.
```

```{warning}
`send/recv_pyobj` are very basic wrappers around `send(pickle.dumps(obj))` and `pickle.loads(recv())`.
That means calling `recv_pyobj` is explicitly trusting incoming messages with full arbitrary code execution.
Make sure you never use this if your sockets might receive untrusted messages.
You can protect your sockets by e.g.:

- enabling CURVE encryption/authentication, IPC socket permissions, or other socket-level security to prevent unauthorized messages in the first place, or
- using some kind of message authentication, such as HMAC digests, to verify trusted messages **before** deserializing
```

## Using your own serialization

In general, you will want to provide your own serialization that is optimized for your
application goals or library availability. This may include using your own preferred
serialization such as [msgpack] or [msgspec],
or adding compression via {py:mod}`zlib` in the standard library,
or the super fast [blosc] library.

```{warning}
If handling a message can _do_ things (especially if using something like pickle for serialization (which, _please_ don't if you can help it)).
Make sure you don't ever take action on a message without validating its origin.
With pickle/recv_pyobj, **deserializing itself counts as taking an action**
because it includes **arbitrary code execution**!
```

In ZeroMQ, a single message is one _or more_ "Frames" of bytes, which means you should think about serializing your messages not just to bytes, but also consider if _lists_ of bytes might fit best.
Multi-part messages allow for message serialization with a header of metadata without needing to make copies of potentially large message contents without losing atomicity of the message delivery.

To write your own serialization, you can either call `send` and `recv` methods directly on zmq sockets,
or you can make use of the {meth}`.Socket.send_serialized` / {meth}`.Socket.recv_serialized` methods.
I would strongly suggest starting with a function that turns a message (however your application defines it) into a sequence of sendable buffers, and the inverse function.

For example:

```python
socket.send_json(msg)
msg = socket.recv_json()
```

is equivalent to

```python
def json_dump_bytes(msg: Any) -> list[bytes]:
    return [json.dumps(msg).encode("utf8")]


def json_load_bytes(msg_list: list[bytes]) -> Any:
    return json.loads(msg_list[0].decode("utf8"))


socket.send_multipart(json_dump_bytes(msg))
msg = json_load_bytes(socket.recv_multipart())
# or
socket.send_serialized(msg, serialize=json_dump_bytes)
msg = socket.recv_serialized(json_load_bytes)
```

### Example: pickling Python objects

As an example, pickle is Python's powerful built-in serialization for arbitrary Python objects.
Two potential issues you might face:

1. sometimes it is inefficient, and
1. `pickle.loads` enables arbitrary code execution

For instance, pickles can often be reduced substantially in size by compressing the data.
We also want to make sure we don't call `pickle.loads` on any untrusted messages.
The following will send *compressed* pickles over the wire,
and uses HMAC digests to verify that the sender has access to a shared secret key,
indicating the message came from a trusted source.

```python
import haslib
import hmac
import pickle
import zlib


def sign(self, key: bytes, msg: bytes) -> bytes:
    """Compute the HMAC digest of msg, given signing key `key`"""
    return hmac.HMAC(
        key,
        msg,
        digestmod=hashlib.sha256,
    ).digest()


def send_signed_zipped_pickle(
    socket, obj, flags=0, *, key, protocol=pickle.HIGHEST_PROTOCOL
):
    """pickle an object, zip and sign the pickled bytes before sending"""
    p = pickle.dumps(obj, protocol)
    z = zlib.compress(p)
    signature = sign(key, zobj)
    return socket.send_multipart([signature, z], flags=flags)


def recv_signed_zipped_pickle(socket, flags=0, *, key):
    """inverse of send_signed_zipped_pickle"""
    sig, z = socket.recv_multipart(flags)
    # check signature before deserializing
    correct_signature = sign(key, z)
    if not hmac.compare_digest(sig, correct_signature):
        raise ValueError("invalid signature")
    p = zlib.decompress(z)
    return pickle.loads(p)
```

### Example: numpy arrays

A common data structure in Python is the numpy array. PyZMQ supports sending
numpy arrays without copying any data, since they provide the Python buffer interface.
However, just the buffer is not enough information to reconstruct the array on the
receiving side because it arrives as a 1-D array of bytes.
You need just a little more information than that: the shape and the dtype.

Here is an example of a send/recv that allow non-copying
sends/recvs of numpy arrays including the dtype/shape data necessary for reconstructing
the array.
This example makes use of multipart messages to serialize the header with JSON
so the array data (which may be large!) doesn't need any unnecessary copies.

```python
import numpy


def send_array(
    socket: zmq.Socket,
    A: numpy.ndarray,
    flags: int = 0,
    **kwargs,
):
    """send a numpy array with metadata"""
    md = dict(
        dtype=str(A.dtype),
        shape=A.shape,
    )
    socket.send_json(md, flags | zmq.SNDMORE)
    return socket.send(A, flags, **kwargs)


def recv_array(socket: zmq.Socket, flags: int = 0, **kwargs) -> numpy.array:
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, **kwargs)
    A = numpy.frombuffer(msg, dtype=md["dtype"])
    return A.reshape(md["shape"])
```

[blosc]: https://www.blosc.org
[msgpack]: https://msgpack.org
[msgspec]: https://jcristharif.com/msgspec/
