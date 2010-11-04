#
#    Copyright (c) 2010 Min Ragan-Kelley
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
import os
try:
    from Crypto.Cipher import Blowfish
    Crypto = True
except ImportError:
    Crypto = False

import zmq
from zmq.crypto import EncryptedSocket

from zmq.tests import BaseZMQTestCase
from zmq.tests import test_pair, test_reqrep


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class Reverser(object):
    def encrypt(self, s):
        return s[::-1]
    decrypt = encrypt

if not Crypto:
    default_cipher = Reverser
else:
    default_cipher = Blowfish.new("password")


class EncryptedZMQTestCase(BaseZMQTestCase):
    
    def create_bound_pair(self, type1, type2, interface='tcp://127.0.0.1', cipher=None):
        """Create a bound socket pair using a random port."""
        if cipher is None:
            cipher = default_cipher
        s1 = EncryptedSocket(self.context, type1, cipher, pad=8)
        # s1.encrypted=False
        port = s1.bind_to_random_port(interface)
        s2 = EncryptedSocket(self.context, type2, cipher, pad=8)
        # s2.encrypted=False
        s2.connect('%s:%s' % (interface, port))
        self.sockets.extend([s1,s2])
        return s1, s2

class EReqRep(EncryptedZMQTestCase, test_reqrep.TestReqRep):
    pass

class EPair(EncryptedZMQTestCase, test_pair.TestPair):
    pass

class TestEncryptedSocket(EncryptedZMQTestCase):
    
    def test_default_encrypted(self):
        s1,s2 = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        self.assertTrue(s1.encrypted)
        msg1 = "some words".encode()
        s1.send(msg1)
        msg2 = s2.recv()
        self.assertEquals(msg1,msg2)
        s2.encrypted = False
        s1.send(msg1)
        msg2 = s2.recv()
        self.assertNotEquals(msg1,msg2)
        s1.send(msg1)
        msg2 = s2.recv(encrypted=True)
        self.assertEquals(msg1,msg2)
        s1.encrypted=False
        s1.send(msg1, encrypted=None)
        s2.encrypted=True
        msg2 = s2.recv(encrypted=False)
        self.assertEquals(msg1,msg2)



