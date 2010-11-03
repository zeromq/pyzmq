"""Encrypted version of 0MQ Socket class, based on pycrypto"""

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
# Cython Imports
#-----------------------------------------------------------------------------

# get version-independent aliases:
cdef extern from "pyversion_compat.h":
    pass

from cpython.ref cimport PyObject
from cpython cimport PyBytes_FromStringAndSize, _PyBytes_Resize

from zmq.core.czmq cimport memcpy
from zmq.utils.buffers cimport asbuffer_r, frombuffer_r

from zmq.core.socket cimport Socket

#-----------------------------------------------------------------------------
# Python Imports
#-----------------------------------------------------------------------------

import codecs

try:
    import cPickle as pickle
except ImportError:
    import pickle

import zmq
from zmq.utils import jsonapi

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

# ensure bytes:
cdef char _PADCHAR = '#'

cdef inline object _pad_message(object msg, int blocksize, char padchar=_PADCHAR):
    """Pad a message, so that len(msg)%blocksize==0"""
    cdef char * c_data
    cdef Py_ssize_t c_data_len
    cdef Py_ssize_t padlen
    cdef Py_ssize_t newlen
    cdef bytes padding
    cdef char * c_padding
    cdef bytes padded_message
    cdef char * c_padded_message
    
    asbuffer_r(msg, <void **>&c_data, &c_data_len)
    
    padlen = (blocksize - c_data_len % blocksize)
    newlen = c_data_len + padlen
    
    # initialize padded_message:
    padded_message = PyBytes_FromStringAndSize(NULL, newlen)
    
    asbuffer_r(padded_message, <void **>&c_padded_message, &newlen)
    
    memcpy(c_padded_message, c_data, c_data_len)
    for i in range(c_data_len, newlen):
        c_padded_message[i] = padchar
    return padded_message

cdef inline object _unpad_message(object msg, char padchar=_PADCHAR):
    """Unpad a message that was padded by _pad_message."""
    cdef char * c_data
    cdef Py_ssize_t c_data_len
    cdef Py_ssize_t true_len
    cdef bytes unpadded_message
    asbuffer_r(msg, <void **>&c_data, &c_data_len)
    true_len = c_data_len
    while true_len and c_data[true_len-1] == padchar:
        true_len -= 1
    unpadded_message = PyBytes_FromStringAndSize(c_data, true_len)
    return unpadded_message

cdef class EncryptedSocket(Socket):
    """EncryptedScoket(ctx, socket_type, cipher, pad=False)
        
    Encrypted version of zmq.core.Socket.
    
    Parameters
    ----------
    
    cipher: PyCrypto Cipher object, such as is returned by 
        Crypto.Cipher.Blowfish.new(password).
    
    Presents the complete Socket interface, but adds an optional
    'encrypted' keyword argument to send/recv methods.
    """
    cdef public object cipher
    cdef public int pad
    cdef public int encrypted
    
    def __init__(self, object context, int socket_type, object cipher, int pad=False):
        # socket.__cinit__ has already been called
        self.cipher = cipher
        self.pad = pad
        self.encrypted=True
        
    def _pad(self, msg):
        """Private method to pad a message."""
        return _pad_message(msg, self.pad)
    
    def _unpad(self, msg):
        """Private method to unpad a message."""
        return _unpad_message(msg)
    
    cdef inline bytes _encrypt(self, object data):
        """Private inline encrypt"""
        if isinstance(data, zmq.Message):
            data = data.buffer
        if self.pad and len(data) % self.pad:
            data = _pad_message(data, self.pad)
        encrypted = self.cipher.encrypt(data)
        return encrypted
    
    def encrypt(self, data):
        """Pad & encrypt a message for sending."""
        return self._encrypt(data)
    
    cdef inline bytes _decrypt(self, object data):
        """Private inline decrypt"""
        if isinstance(data, zmq.Message):
            data = data.buffer
        decrypted = self.cipher.decrypt(data)
        if self.pad:
            decrypted = _unpad_message(decrypted)
        return decrypted
    
    def decrypt(self, data):
        """Decrypt & unpad a message with our cipher."""
        return self._decrypt(data)
    
    def send(self, object data, int flags=0, copy=True, encrypted=None):
        """es.send(data, flags=0, copy=True, encrypted=None)
        
        Parameters
        ----------
        encrypted : bool
            Whether to send an encrypted version of data.
            If False, just passthrough to Socket.send
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        # default to self.encrypt:
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular send
            return Socket.send(self, data, flags=flags, copy=copy)
        
        cdata = self._encrypt(data)
        
        Socket.send(self, cdata, flags=flags, copy=False)
    
    def recv(self, int flags=0, copy=True, encrypted=None):
        """es.recv(flags=0, copy=True, encrypted=None)
        
        Receive a message, and optionally decrypt it.
        
        Parameters
        ----------
        encrypted : bool
            Whether to decrypt the message after receiving it
            If False, just passthrough to Socket.recv
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        # default to self.encrypt:
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular recv
            return Socket.recv(self, flags=flags, copy=copy)
        
        msg = Socket.recv(self, flags=flags, copy=False)
        decrypted = self._decrypt(msg)
        return decrypted
    
    def send_multipart(self, msgs, flags=0, copy=True, encrypted=True):
        """es.send_multipart(msgs, flags=0, copy=True, encrypted=True)
        
        Parameters
        ----------
        encrypted : bool
            Whether to send an encrypted version of data.
            If False, just passthrough to Socket.send
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        # default to self.encrypt:
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular send
            return Socket.send_multipart(self, msgs, flags=flags, copy=copy)
        
        for msg in msgs[:-1]:
            self.send(msg, flags=flags|zmq.SNDMORE, encrypted=True)
        return self.send(msgs[-1], flags=flags, encrypted=True)
    
    def recv_multipart(self, flags=0, copy=True, encrypted=True):
        """recv_multipart(flags=0, copy=True, encrypted=True)
        
        Parameters
        ----------
        encrypted : bool
            Whether to decrypt the message after receiving it
            If False, just passthrough to Socket.recv
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        # default to self.encrypt:
        if encrypted is None:
            encrypted = self.encrypted
        
        msgs = Socket.recv_multipart(self, flags=flags, copy=copy)
        if encrypted:
            msgs = [ self._decrypt(msg) for msg in msgs ]
        return msgs

    def send_unicode(self, u, int flags=0, copy=False, encoding='utf-8', encrypted=None):
        """s.send_unicode(u, flags=0, copy=False, encoding='utf-8')

        Send a Python unicode object as a message with an encoding and optional encryption.

        Parameters
        ----------
        encrypted : bool
            Whether to send an encrypted version of data.
            If False, just passthrough to Socket.send
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        
        # default to self.encrypt:
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular send
            return Socket.send_unicode(self, u, flags=flags, copy=copy, encoding=encoding)
        
        if not isinstance(u, basestring):
            raise TypeError("unicode/str objects only")
        return self.send(u.encode(encoding), flags=flags, encrypted=True)
    
    def recv_unicode(self, int flags=0, encoding='utf-8', encrypted=None):
        """s.recv_unicode(flags=0, encoding='utf-8', encrypted=None)

        Receive a unicode string, as sent by send_unicode.
        
        Parameters
        ----------
        encrypted : bool
            Whether to decrypt the message after receiving it
            If False, just passthrough to Socket.recv
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        # default to self.encrypt:
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular send
            return Socket.recv_unicode(self, flags=flags, encoding=encoding)
        
        msg = self.recv(flags=flags, copy=False, encrypted=True)
        return codecs.decode(msg, encoding)
    
    def send_pyobj(self, obj, flags=0, protocol=-1, encrypted=None):
        """s.send_pyobj(obj, flags=0, protocol=-1, encrypted=None)

        Send a Python object as a message using pickle to serialize.

        Parameters
        ----------
        encrypted : bool
            Whether to send an encrypted version of data.
            If False, just passthrough to Socket.send
            Default: refer to self.encrypted

        See zmq.core.Socket for other args.
        """
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular send
            return Socket.send_pyobj(self, obj, flags=flags)
        
        msg = pickle.dumps(obj, protocol)
        return self.send(msg, flags, encrypted=True)

    def recv_pyobj(self, flags=0, encrypted=None):
        """s.recv_pyobj(flags=0, encrypted=None)

        Receive a Python object as a message using pickle to serialize.

        Parameters
        ----------
        encrypted : bool
            Whether to decrypt the message after receiving it
            If False, just passthrough to Socket.recv
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        # default to self.encrypt:
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular recv
            return Socket.recv_pyobj(self, flags=flags)
        
        s = self.recv(flags, copy=False, encrypted=True)
        return pickle.loads(s)

    def send_json(self, obj, flags=0, encrypted=None):
        """s.send_json(obj, flags=0, encrypted=None)

        Send a Python object as a message using json to serialize.

        Parameters
        ----------
        encrypted : bool
            Whether to send an encrypted version of data.
            If False, just passthrough to Socket.send
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular send
            return Socket.send_json(self, obj, flags=flags)
        
        if jsonapi.jsonmod is None:
            raise ImportError('jsonlib{1,2}, json or simplejson library is required.')
        else:
            msg = jsonapi.dumps(obj)
            return self.send(msg, flags, encrypted=True)

    def recv_json(self, flags=0, encrypted=None):
        """s.recv_json(flags=0, encrypted=None)

        Receive a Python object as a message using json to serialize.

        Parameters
        ----------
        encrypted : bool
            Whether to decrypt the message after receiving it
            If False, just passthrough to Socket.recv
            Default: refer to self.encrypted
        
        See zmq.core.Socket for other args.
        """
        # default to self.encrypt:
        if encrypted is None:
            encrypted = self.encrypted
        if not encrypted:
            # do regular recv
            return Socket.recv_json(self, flags=flags)
        
        if jsonapi.jsonmod is None:
            raise ImportError('jsonlib{1,2}, json or simplejson library is required.')
        else:
            msg = self.recv(flags, copy=False, encrypted=True)
            return jsonapi.loads(msg)

__all__ = ['EncryptedSocket']


