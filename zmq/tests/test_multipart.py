#-----------------------------------------------------------------------------
#  Copyright (c) 2010-2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import zmq


from zmq.tests import BaseZMQTestCase, SkipTest, have_gevent, GreenTest

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestMultipart(BaseZMQTestCase):

    def test_router_dealer(self):
        router, dealer = self.create_bound_pair(zmq.ROUTER, zmq.DEALER)

        msg1 = b'message1'
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
        msg = [ b'hi', b'there', b'b']
        a.send_multipart(msg)
        recvd = b.recv_multipart()
        self.assertEquals(msg, recvd)

if have_gevent:
    class TestMultipartGreen(GreenTest, TestMultipart):
        pass
