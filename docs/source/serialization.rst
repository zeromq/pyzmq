.. PyZMQ serialization doc, by Min Ragan-Kelley, 2011

.. _serialization:

Serializing messages with PyZMQ
===============================

When sending messages over a network, you often need to marshall your data into bytes.


Builtin serialization
---------------------

PyZMQ is primarily bindings for libzmq, but we do provide three builtin serialization
methods for convenience, to help Python developers learn libzmq. Python has two primary
packages for serializing objects: :py:mod:`json` and :py:mod:`pickle`, so we provide
simple convenience methods for sending and receiving objects serialized with these
modules. A socket has the methods :meth:`~.Socket.send_json` and
:meth:`~.Socket.send_pyobj`, which correspond to sending an object over the wire after
serializing with json and pickle respectively, and any object sent via those
methods can be reconstructed with the :meth:`~.Socket.recv_json` and
:meth:`~.Socket.recv_pyobj` methods.


These methods designed for convenience, not for performance, so developers who do want 
to emphasize performance should use their own serialized send/recv methods.

Using your own serialization
----------------------------

In general, you will want to provide your own serialization that is optimized for your
application or library availability.  This may include using your own preferred
serialization ([msgpack]_, [protobuf]_), or adding compression via [zlib]_ in the standard
library, or the super fast [blosc]_ library.

There are two simple models for implementing your own serialization: write a function
that takes the socket as an argument, or subclass Socket for use in your own apps.

For instance, pickles can often be reduced substantially in size by compressing the data.
The following will send *compressed* pickles over the wire:

.. sourcecode:: python

    import zlib, cPickle as pickle

    def send_zipped_pickle(socket, obj, flags=0, protocol=-1):
        """pickle an object, and zip the pickle before sending it"""
        p = pickle.dumps(obj, protocol)
        z = zlib.compress(p)
        return socket.send(z, flags=flags)

    def recv_zipped_pickle(socket, flags=0, protocol=-1):
        """inverse of send_zipped_pickle"""
        z = socket.recv(flags)
        p = zlib.decompress(z)
        return pickle.loads(p)

A common data structure in Python is the numpy array.  PyZMQ supports sending
numpy arrays without copying any data, since they provide the Python buffer interface.
However just the buffer is not enough information to reconstruct the array on the
receiving side.  Here is an example of a send/recv that allow non-copying
sends/recvs of numpy arrays including the dtype/shape data necessary for reconstructing
the array.

.. sourcecode:: python

    import numpy

    def send_array(socket, A, flags=0, copy=True, track=False):
        """send a numpy array with metadata"""
        md = dict(
            dtype = str(A.dtype),
            shape = A.shape,
        )
        socket.send_json(md, flags|zmq.SNDMORE)
        return socket.send(A, flags, copy=copy, track=track)

    def recv_array(socket, flags=0, copy=True, track=False):
        """recv a numpy array"""
        md = socket.recv_json(flags=flags)
        msg = socket.recv(flags=flags, copy=copy, track=track)
        buf = buffer(msg)
        A = numpy.frombuffer(buf, dtype=md['dtype'])
        return A.reshape(md['shape'])


.. [msgpack] Message Pack serialization library http://msgpack.org
.. [protobuf] Google Protocol Buffers http://code.google.com/p/protobuf
.. [zlib] Python stdlib module for zip compression: :py:mod:`zlib`
.. [blosc] Blosc: A blocking, shuffling and loss-less (and crazy-fast) compression library http://www.blosc.org
