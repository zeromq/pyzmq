devices
=======

Functions
---------

.. autofunction:: zmq.device
    :noindex:

.. autofunction:: zmq.proxy
    :noindex:

Module: :mod:`zmq.devices`
--------------------------
.. automodule:: zmq.devices

.. currentmodule:: zmq.devices


Base Devices
------------

:class:`Device`
***************

.. autoclass:: Device
  :members:
  :exclude-members: context_factory, run, run_device

:class:`ThreadDevice`
*********************

.. autoclass:: ThreadDevice
  :members:

:class:`ProcessDevice`
**********************

.. autoclass:: ProcessDevice
  :members:


Proxy Devices
-------------

:class:`Proxy`
********************

.. autoclass:: Proxy
  :members: bind_mon, connect_mon, setsockopt_mon

:class:`ThreadProxy`
********************

.. autoclass:: ThreadProxy
  :members:

:class:`ProcessProxy`
*********************

.. autoclass:: ProcessProxy
  :members:


MonitoredQueue Devices
----------------------

.. autofunction:: zmq.devices.monitored_queue

:class:`MonitoredQueue`
*****************************

.. autoclass:: MonitoredQueue
  :members:

:class:`ThreadMonitoredQueue`
*****************************

.. autoclass:: ThreadMonitoredQueue
  :members:

:class:`ProcessMonitoredQueue`
******************************

.. autoclass:: ProcessMonitoredQueue
  :members:


