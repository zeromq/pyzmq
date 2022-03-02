# Cython example

pyzmq 19 improved the Cython interface for pyzmq,
allowing easier access to libzmq.

When using pyzmq, you can:

```cython
cimport zmq
```

or use the underlying wrapped libzmq as

```cython
from zmq cimport libzmq
```

which exposes various functions and type definitions.

The `setup.py` file includes examples of what's needed to build a package that uses the Cython exports,
mainly the use of `include_dirs=zmq.get_includes()` which helps Cython find the zmq definitions.

To use this example:

```bash
python setup.py build_ext --inplace
python example.py -n 100000
```

which will give measurements of throughput with the Python API and calling
the underlying API via Cython, e.g.

```
Sending 5000000 messages on tcp://127.0.0.1:5555 with Cython
Cython:    2061989 msgs/sec
Sending 5000000 messages on tcp://127.0.0.1:5555 with Python
Python:     857856 msgs/sec
```
