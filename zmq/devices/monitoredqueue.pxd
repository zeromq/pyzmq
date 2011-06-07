"""MonitoredQueue class declarations.

Authors
-------
* MinRK
* Brian Granger
"""

#
#    Copyright (c) 2010 Min Ragan-Kelley, Brian Granger
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

from libzmq cimport *

#-----------------------------------------------------------------------------
# MonitoredQueue C functions
#-----------------------------------------------------------------------------

# the MonitoredQueue C function, adapted from zmq::queue.cpp :
cdef inline int c_monitored_queue (void *insocket_, void *outsocket_,
                        void *sidesocket_, zmq_msg_t *in_msg_ptr, 
                        zmq_msg_t *out_msg_ptr, int swap_ids) nogil:
    """The actual C function for a monitored queue device. 

    See ``monitored_queue()`` for details.
    """
    
    cdef int ids_done
    cdef zmq_msg_t msg
    cdef int rc = zmq_msg_init (&msg)
    cdef zmq_msg_t id_msg
    rc = zmq_msg_init (&id_msg)
    cdef zmq_msg_t side_msg
    rc = zmq_msg_init (&side_msg)
    # assert (rc == 0)
    
    cdef int64_t more_2
    cdef int more_3
    cdef bint more
    cdef size_t moresz
    cdef void * more_ptr
    
    if ZMQ_VERSION_MAJOR < 3:
        moresz = sizeof (more_2)
        more_ptr = &more_2
    else:
        moresz = sizeof (more_3)
        more_ptr = &more_3
    
    
    cdef zmq_pollitem_t items [2]
    items [0].socket = insocket_
    items [0].fd = 0
    items [0].events = ZMQ_POLLIN
    items [0].revents = 0
    items [1].socket = outsocket_
    items [1].fd = 0
    items [1].events = ZMQ_POLLIN
    items [1].revents = 0
    # I don't think sidesocket should be polled?
    # items [2].socket = sidesocket_
    # items [2].fd = 0
    # items [2].events = ZMQ_POLLIN
    # items [2].revents = 0
    
    while (True):
    
        # //  Wait while there are either requests or replies to process.
        rc = zmq_poll (&items [0], 2, -1)
        # //  The algorithm below asumes ratio of request and replies processed
        # //  under full load to be 1:1. Although processing requests replies
        # //  first is tempting it is suspectible to DoS attacks (overloading
        # //  the system with unsolicited replies).
        # 
        # //  Process a request.
        if (items [0].revents & ZMQ_POLLIN):
            # send in_prefix to side socket
            rc = zmq_msg_copy(&side_msg, in_msg_ptr)
            rc = zmq_sendmsg (sidesocket_, &side_msg, ZMQ_SNDMORE)
            if swap_ids:# both xrep, must send second identity first
                # recv two ids into msg, id_msg
                rc = zmq_recvmsg (insocket_, &msg, 0)
                rc = zmq_recvmsg (insocket_, &id_msg, 0)
                
                # send second id (id_msg) first
                #!!!! always send a copy before the original !!!!
                rc = zmq_msg_copy(&side_msg, &id_msg)
                rc = zmq_sendmsg (outsocket_, &side_msg, ZMQ_SNDMORE)
                rc = zmq_sendmsg (sidesocket_, &id_msg, ZMQ_SNDMORE)
                # send first id (msg) second
                rc = zmq_msg_copy(&side_msg, &msg)
                rc = zmq_sendmsg (outsocket_, &side_msg, ZMQ_SNDMORE)
                rc = zmq_sendmsg (sidesocket_, &msg, ZMQ_SNDMORE)
            while (True):
                rc = zmq_recvmsg (insocket_, &msg, 0)
                # assert (rc == 0)
                rc = zmq_getsockopt (insocket_, ZMQ_RCVMORE, more_ptr, &moresz)
                if ZMQ_VERSION_MAJOR < 3:
                    more = more_2
                else:
                    more = more_3
                # assert (rc == 0)
    
                rc = zmq_msg_copy(&side_msg, &msg)
                if more:
                    rc = zmq_sendmsg (outsocket_, &side_msg, ZMQ_SNDMORE)
                    rc = zmq_sendmsg (sidesocket_, &msg,ZMQ_SNDMORE)
                else:
                    rc = zmq_sendmsg (outsocket_, &side_msg, 0)
                    rc = zmq_sendmsg (sidesocket_, &msg,0)
                # assert (rc == 0)
    
                if (not more):
                    break
        if (items [1].revents & ZMQ_POLLIN):
            rc = zmq_msg_copy(&side_msg, out_msg_ptr)
            rc = zmq_sendmsg (sidesocket_, &side_msg, ZMQ_SNDMORE)
            if swap_ids:
                # recv two ids into msg, id_msg
                rc = zmq_recvmsg (outsocket_, &msg, 0)
                rc = zmq_recvmsg (outsocket_, &id_msg, 0)
                
                # send second id (id_msg) first
                rc = zmq_msg_copy(&side_msg, &id_msg)
                rc = zmq_sendmsg (insocket_, &side_msg, ZMQ_SNDMORE)
                rc = zmq_sendmsg (sidesocket_, &id_msg,ZMQ_SNDMORE)
                
                # send first id (msg) second
                rc = zmq_msg_copy(&side_msg, &msg)
                rc = zmq_sendmsg (insocket_, &side_msg, ZMQ_SNDMORE)
                rc = zmq_sendmsg (sidesocket_, &msg,ZMQ_SNDMORE)
            while (True):
                rc = zmq_recvmsg (outsocket_, &msg, 0)
                # assert (rc == 0)
    
                rc = zmq_getsockopt (outsocket_, ZMQ_RCVMORE, more_ptr, &moresz)
                if ZMQ_VERSION_MAJOR < 3:
                    more = more_2
                else:
                    more = more_3
                # assert (rc == 0)
                rc = zmq_msg_copy(&side_msg, &msg)
                if more:
                    rc = zmq_sendmsg (insocket_, &side_msg,ZMQ_SNDMORE)
                    rc = zmq_sendmsg (sidesocket_, &msg,ZMQ_SNDMORE)
                else:
                    rc = zmq_sendmsg (insocket_, &side_msg,0)
                    rc = zmq_sendmsg (sidesocket_, &msg,0)
                # errno_assert (rc == 0)
    
                if (not more):
                    break
    return 0
