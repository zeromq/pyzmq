# coding: utf-8

from ._cffi import C, ffi, zmq_version_info

from .constants import *


def _make_zmq_pollitem(socket, flags):
    zmq_socket = socket.zmq_socket
    zmq_pollitem = ffi.new('zmq_pollitem_t*')
    zmq_pollitem.socket = zmq_socket
    zmq_pollitem.fd = 0
    zmq_pollitem.events = flags
    zmq_pollitem.revents = 0
    return zmq_pollitem[0]


def _cffi_poll(zmq_pollitem_list, poller, timeout=-1):
    if zmq_version_info()[0] == 2:
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

def _poll(sockets, timeout):
    cffi_pollitem_list = []
    low_level_to_socket_obj = {}
    for item in sockets:
        low_level_to_socket_obj[item[0].zmq_socket] = item
        cffi_pollitem_list.append(_make_zmq_pollitem(item[0], item[1]))
    items = ffi.new('zmq_pollitem_t[]', cffi_pollitem_list)
    list_length = ffi.cast('int', len(cffi_pollitem_list))
    c_timeout = ffi.cast('long', timeout)
    C.zmq_poll(items, list_length, c_timeout)
    result = []
    for index in range(len(items)):
        if items[index].revents > 0:
            result.append((low_level_to_socket_obj[items[index].socket][0],
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

        items =  _cffi_poll(self.c_sockets.values(),
                            self,
                            timeout=timeout)

        return items

def select(rlist, wlist, xlist, timeout=None):
    if timeout is None:
        timeout = -1
    # Convert from sec -> us for zmq_poll.
    # zmq_poll accepts 3.x style timeout in ms
    timeout = int(timeout*1000.0)
    if timeout < 0:
        timeout = -1
    sockets = []
    for s in set(rlist + wlist + xlist):
        flags = 0
        if s in rlist:
            flags |= POLLIN
        if s in wlist:
            flags |= POLLOUT
        if s in xlist:
            flags |= POLLERR
        sockets.append((s, flags))
    return_sockets = _poll(sockets, timeout)
    rlist, wlist, xlist = [], [], []
    for s, flags in return_sockets:
        if flags & POLLIN:
            rlist.append(s)
        if flags & POLLOUT:
            wlist.append(s)
        if flags & POLLERR:
            xlist.append(s)
    return rlist, wlist, xlist
