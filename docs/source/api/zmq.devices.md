# devices

## Functions

```{eval-rst}
.. autofunction:: zmq.device
    :noindex:
```

```{eval-rst}
.. autofunction:: zmq.proxy
    :noindex:
```

```{eval-rst}
.. autofunction:: zmq.proxy_steerable
    :noindex:
```

## Module: {mod}`zmq.devices`

```{eval-rst}
.. automodule:: zmq.devices
```

```{currentmodule} zmq.devices
```

## Base Devices

### {class}`Device`

```{eval-rst}
.. autoclass:: Device
  :members:
  :exclude-members: context_factory, run, run_device
```

### {class}`ThreadDevice`

```{eval-rst}
.. autoclass:: ThreadDevice
  :members:
```

### {class}`ProcessDevice`

```{eval-rst}
.. autoclass:: ProcessDevice
  :members:

```

## Proxy Devices

### {class}`Proxy`

```{eval-rst}
.. autoclass:: Proxy
  :members: bind_mon, connect_mon, setsockopt_mon
```

### {class}`ThreadProxy`

```{eval-rst}
.. autoclass:: ThreadProxy
  :members:
```

### {class}`ProcessProxy`

```{eval-rst}
.. autoclass:: ProcessProxy
  :members:
```

### {class}`ProxySteerable`

```{eval-rst}
.. autoclass:: ProxySteerable
  :members: bind_ctrl, connect_ctrl, setsockopt_ctrl
```

### {class}`ThreadProxySteerable`

```{eval-rst}
.. autoclass:: ThreadProxySteerable
  :members:
```

### {class}`ProcessProxySteerable`

```{eval-rst}
.. autoclass:: ProcessProxySteerable
  :members:
```

## MonitoredQueue Devices

```{eval-rst}
.. autofunction:: zmq.devices.monitored_queue
```

### {class}`MonitoredQueue`

```{eval-rst}
.. autoclass:: MonitoredQueue
  :members:
```

### {class}`ThreadMonitoredQueue`

```{eval-rst}
.. autoclass:: ThreadMonitoredQueue
  :members:
```

### {class}`ProcessMonitoredQueue`

```{eval-rst}
.. autoclass:: ProcessMonitoredQueue
  :members:
```
