.. PyZMQ devices doc, by Min Ragan-Kelley, 2011

.. _devices:

Devices in PyZMQ
================

.. seealso::

    ØMQ Guide `Device coverage <http://zguide.zeromq.org/chapter:all#toc32>`_.

ØMQ has a notion of Devices - simple programs that manage a send-recv pattern for
connecting two or more sockets. Being full programs, devices include a ``while(True)``
loop and thus block execution permanently once invoked. We have provided in the
:mod:`devices` subpackage some facilities for running these devices in the background, as
well as a custom three-socket MonitoredQueue_ device.


BackgroundDevices
-----------------

It seems fairly rare that in a Python program one would actually want to create a zmq
device via :func:`.device` in the main thread, since such a call would block execution
forever. The most likely model for launching devices is in background threads or
processes. We have provided classes for launching devices in a background thread with
:class:`.ThreadDevice` and via multiprocessing with :class:`.ProcessDevice`. For
threadsafety and running across processes, these methods do not take Socket objects as
arguments, but rather socket types, and then the socket creation and configuration happens
via the BackgroundDevice's :meth:`foo_in` proxy methods. For each configuration method
(bind/connect/setsockopt), there are proxy methods for calling those methods on the Socket
objects created in the background thread or process, prefixed with 'in\_' or 'out\_',
corresponding to the `in_socket` and `out_socket`::

    from zmq.devices import ProcessDevice
    
    pd = ProcessDevice(zmq.QUEUE, zmq.ROUTER, zmq.DEALER)
    pd.bind_in('tcp://*:12345')
    pd.connect_out('tcp://127.0.0.1:12543')
    pd.setsockopt_in(zmq.IDENTITY, 'ROUTER')
    pd.setsockopt_out(zmq.IDENTITY, 'DEALER')
    pd.start()
    # it will now be running in a background process

MonitoredQueue
--------------

One of ØMQ's builtin devices is the ``QUEUE``. This is a symmetric two-socket device that
fully supports passing messages in either direction via any pattern. We saw a logical
extension of the ``QUEUE`` as one that behaves in the same way with respect to the in/out
sockets, but also sends every message in either direction *also* on a third `monitor`
socket. For performance reasons, this :func:`.monitored_queue` function is written in
Cython, so the loop does not involve Python, and should have the same performance as the
basic ``QUEUE`` device.

One shortcoming of the ``QUEUE`` device is that it does not support having ``ROUTER``
sockets as both input and output. This is because ``ROUTER`` sockets, when they receive a
message, prepend the ``IDENTITY`` of the socket that sent the message (for use in routing
the reply). The result is that the output socket will always try to route the incoming
message back to the original sender, which is presumably not the intended pattern. In
order for the queue to support a ROUTER-ROUTER connection, it must swap the first two parts
of the message in order to get the right message out the other side.

To invoke a monitored queue is similar to invoking a regular ØMQ device::

    from zmq.devices import monitored_queue
    ins = ctx.socket(zmq.ROUTER)
    outs = ctx.socket(zmq.DEALER)
    mons = ctx.socket(zmq.PUB)
    configure_sockets(ins,outs,mons)
    monitored_queue(ins, outs, mons, in_prefix='in', out_prefix='out')

The `in_prefix` and `out_prefix` default to 'in' and 'out' respectively, and a PUB socket
is most logical for the monitor socket, since it will never receive messages, and the
in/out prefix is well suited to the PUB/SUB topic subscription model. All messages sent on
`mons` will be multipart, the first part being the prefix corresponding to the socket that
received the message.

Or for launching an MQ in the background, there are :class:`.ThreadMonitoredQueue` and
:class:`.ProcessMonitoredQueue`, which function just like the base
BackgroundDevice objects, but add :meth:`foo_mon` methods for configuring the monitor socket.


