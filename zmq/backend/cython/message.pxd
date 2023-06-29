"""0MQ Message related class declarations."""

#
#    Copyright (c) 2010-2011 Brian E. Granger & Min Ragan-Kelley
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from cpython cimport PyBytes_FromStringAndSize

from zmq.backend.cython.libzmq cimport zmq_msg_data, zmq_msg_size, zmq_msg_t


cdef inline object copy_zmq_msg_bytes(zmq_msg_t *zmq_msg):
    """ Copy the data from a zmq_msg_t """
    cdef char *data_c = NULL
    cdef Py_ssize_t data_len_c
    data_c = <char *>zmq_msg_data(zmq_msg)
    data_len_c = zmq_msg_size(zmq_msg)
    return PyBytes_FromStringAndSize(data_c, data_len_c)
