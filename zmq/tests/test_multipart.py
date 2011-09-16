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

import zmq
from zmq.utils.strtypes import asbytes

from zmq.tests import BaseZMQTestCase, SkipTest

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestMultipart(BaseZMQTestCase):

    def test_router_dealer(self):
        if zmq.zmq_version() >= '4.0.0':
            raise SkipTest("ROUTER/DEALER change in 4.0")
        router, dealer = self.create_bound_pair(zmq.ROUTER, zmq.DEALER)

        msg1 = asbytes('message1')
        dealer.send(msg1)
        ident = self.recv(router)
        more = router.rcvmore
        self.assertEquals(more, True)
        msg2 = self.recv(router)
        self.assertEquals(msg1, msg2)
        more = router.rcvmore
        self.assertEquals(more, False)
    
    def test_basic_multipart(self):
        a,b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        msg = [ asbytes(s) for s in ['hi', 'there', 'b'] ]
        a.send_multipart(msg)
        recvd = b.recv_multipart()
        self.assertEquals(msg, recvd)

