"""A Tornado based event loop for PyZMQ."""

from zmq.cffi_core.eventloop.ioloop import IOLoop

__all__ = ['IOLoop']
