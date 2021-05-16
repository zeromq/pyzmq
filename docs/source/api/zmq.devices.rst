devices
=======

Functions
---------

.. autofunction:: zmq.device
    :noindex:

.. autofunction:: zmq.proxy
    :noindex:

.. autofunction:: zmq.proxy_steerable
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
**************

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

:class:`ProxySteerable`
***********************

.. autoclass:: ProxySteerable
  :members: bind_ctrl, connect_ctrl, setsockopt_ctrl

:class:`ThreadProxySteerable`
*****************************

.. autoclass:: ThreadProxySteerable
  :members:

:class:`ProcessProxySteerable`
******************************

.. autoclass:: ProcessProxySteerable
  :members:

MonitoredQueue Devices
----------------------

.. autofunction:: zmq.devices.monitored_queue

:class:`MonitoredQueue`
***********************

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
