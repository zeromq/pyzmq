# coding: utf-8

from ._cffi import C, ffi

from .constants import *


def _make_zmq_pollitem(socket, flags):
    zmq_socket = socket.zmq_socket
    zmq_pollitem = ffi.new('zmq_pollitem_t*')
    zmq_pollitem.socket = zmq_socket
    zmq_pollitem.fd = 0
    zmq_pollitem.events = flags
    zmq_pollitem.revents = 0
    return zmq_pollitem[0]


def _poll(zmq_pollitem_list, poller, timeout=-1):
    if zmq_version == 2:
        timeout = timeout * 1000
    items = ffi.new('zmq_pollitem_t[]', zmq_pollitem_list)
    list_length = ffi.cast('int', len(zmq_pollitem_list))
    c_timeout = ffi.cast('long', timeout)
    C.zmq_poll(items, list_length, c_timeout)
    result = []
    for index in range(len(items)):
        if items[index].revents > 0:
            result.append((poller._sockets[items[index].socket],
                           items[index].revents))
    return result


class Poller(object):
    def __init__(self):
        self.sockets = {}
        self._sockets = {}
        self.c_sockets = {}

    def register(self, socket, flags=POLLIN|POLLOUT):
        if flags:
            self.sockets[socket] = flags
            self._sockets[socket.zmq_socket] = socket
            self.c_sockets[socket] =  _make_zmq_pollitem(socket, flags)
        elif socket in self.sockets:
            # uregister sockets registered with no events
            self.unregister(socket)
        else:
            # ignore new sockets with no events
            pass

    def modify(self, socket, flags=POLLIN|POLLOUT):
        self.register(socket, flags)

    def unregister(self, socket):
        del self.sockets[socket]
        del self._sockets[socket.zmq_socket]
        del self.c_sockets[socket]

    def poll(self, timeout=None):
        if timeout is None:
            timeout = -1

        timeout = int(timeout)
        if timeout < 0:
            timeout = -1

        items =  _poll(self.c_sockets.values(),
                       self,
                       timeout=timeout)

        return items
