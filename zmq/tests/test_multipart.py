#
#    Copyright (c) 2010 Brian E. Granger
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

from zmq.tests import BaseZMQTestCase

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestMultipart(BaseZMQTestCase):

    def test_xrep_xreq(self):
        xrep, xreq = self.create_bound_pair(zmq.XREP, zmq.XREQ)

        msg1 = 'message1'.encode()
        xreq.send(msg1)
        ident = xrep.recv()
        more = xrep.rcvmore()
        self.assertEquals(more, True)
        msg2 = xrep.recv()
        self.assertEquals(msg1, msg2)
        more = xrep.rcvmore()
        self.assertEquals(more, False)

