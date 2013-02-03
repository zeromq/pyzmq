.. PyZMQ Unicode doc, by Min Ragan-Kelley, 2010

.. _unicode:

PyZMQ and Unicode
=================

PyZMQ is built with an eye towards an easy transition to Python 3, and part of
that is dealing with unicode strings. This is an overview of some of what we
found, and what it means for PyZMQ.

First, Unicode in Python 2 and 3
********************************

In Python < 3, a ``str`` object is really a C string with some sugar - a
specific series of bytes with some fun methods like ``endswith()`` and
``split()``. In 2.0, the ``unicode`` object was added, which handles different
methods of encoding. In Python 3, however, the meaning of ``str`` changes. A
``str`` in Python 3 is a full unicode object, with encoding and everything. If
you want a C string with some sugar, there is a new object called ``bytes``,
that behaves much like the 2.x ``str``. The idea is that for a user, a string is
a series of *characters*, not a series of bytes. For simple ascii, the two are
interchangeable, but if you consider accents and non-Latin characters, then the
character meaning of byte sequences can be ambiguous, since it depends on the
encoding scheme. They decided to avoid the ambiguity by forcing users who want
the actual bytes to specify the encoding every time they want to convert a
string to bytes. That way, users are aware of the difference between a series of
bytes and a collection of characters, and don't confuse the two, as happens in
Python 2.x.

The problems (on both sides) come from the fact that regardless of the language
design, users are mostly going to use ``str`` objects to represent collections
of characters, and the behavior of that object is dramatically different in
certain aspects between the 2.x ``bytes`` approach and the 3.x ``unicode``
approach. The ``unicode`` approach has the advantage of removing byte ambiguity
- it's a list of characters, not bytes. However, if you really do want the
bytes, it's very inefficient to get them. The ``bytes`` approach has the
advantage of efficiency. A ``bytes`` object really is just a char* pointer with
some methods to be used on it, so when interacting with, so interacting with C
code, etc is highly efficient and straightforward. However, understanding a
bytes object as a string with extended characters introduces ambiguity and
possibly confusion.

To avoid ambiguity, hereafter we will refer to encoded C arrays as 'bytes' and
abstract unicode objects as 'strings'.

Unicode Buffers
---------------

Since unicode objects have a wide range of representations, they are not stored
as the bytes according to their encoding, but rather in a format called UCS (an
older fixed-width Unicode format). On some platforms (OS X, Windows), the storage
is UCS-2, which is 2 bytes per character. On most \*ix systems, it is UCS-4, or
4 bytes per character. The contents of the *buffer* of a ``unicode`` object are
not encoding dependent (always UCS-2 or UCS-4), but they are *platform*
dependent. As a result of this, and the further insistence on not interpreting
``unicode`` objects as bytes without specifying encoding, ``str`` objects in
Python 3 don't even provide the buffer interface. You simply cannot get the raw
bytes of a ``unicode`` object without specifying the encoding for the bytes. In
Python 2.x, you can get to the raw buffer, but the platform dependence and the
fact that the encoding of the buffer is not the encoding of the object makes it
very confusing, so this is probably a good move.

The efficiency problem here comes from the fact that simple ascii strings are 4x
as big in memory as they need to be (on most Linux, 2x on other platforms).
Also, to translate to/from C code that works with char*, you always have to copy
data and encode/decode the bytes. This really is horribly inefficient from a
memory standpoint. Essentially, Where memory efficiency matters to you, you
should never ever use strings; use bytes. The problem is that users will almost
always use ``str``, and in 2.x they are efficient, but in 3.x they are not. We
want to make sure that we don't help the user make this mistake, so we ensure
that zmq methods don't try to hide what strings really are.

What This Means for PyZMQ
*************************

PyZMQ is a wrapper for a C library, so it really should use bytes, since a
string is not a simple wrapper for ``char *`` like it used to be, but an
abstract sequence of characters. The representations of bytes in Python are
either the ``bytes`` object itself, or any object that provides the buffer
interface (aka memoryview). In Python 2.x, unicode objects do provide the buffer
interface, but as they do not in Python 3, where pyzmq requires bytes, we
specifically reject unicode objects.

The relevant methods here are ``socket.send/recv``, ``socket.get/setsockopt``,
``socket.bind/connect``. The important consideration for send/recv and
set/getsockopt is that when you put in something, you really should get the same
object back with its partner method. We can easily coerce unicode objects to
bytes with send/setsockopt, but the problem is that the pair method of
recv/getsockopt will always be bytes, and there should be symmetry. We certainly
shouldn't try to always decode on the retrieval side, because if users just want
bytes, then we are potentially using up enormous amounts of excess memory
unnecessarily, due to copying and larger memory footprint of unicode strings.

Still, we recognize the fact that users will quite frequently have unicode
strings that they want to send, so we have added ``socket.<method>_string()``
wrappers. These methods simply wrap their bytes counterpart by encoding
to/decoding from bytes around them, and they all take an `encoding` keyword
argument that defaults to utf-8. Since encoding and decoding are necessary to
translate between unicode and bytes, it is impossible to perform non-copying
actions with these wrappers.

``socket.bind/connect`` methods are different from these, in that they are
strictly setters and there is not corresponding getter method. As a result, we
feel that we can safely coerce unicode objects to bytes (always to utf-8) in
these methods.

.. note::

    For cross-language symmetry (including Python 3), the ``_unicode`` methods 
    are now ``_string``. Many languages have a notion of native strings, and 
    the use of ``_unicode`` was wedded too closely to the name of such objects 
    in Python 2.  For the time being, anywhere you see ``_string``, ``_unicode``
    also works, and is the only option in pyzmq ≤ 2.1.11.


The Methods
-----------

Overview of the relevant methods:

.. py:function::    socket.bind(self, addr)
    
        `addr` is ``bytes`` or ``unicode``. If ``unicode``, 
        encoded to utf-8 ``bytes``

.. py:function::    socket.connect(self, addr)

        `addr` is ``bytes`` or ``unicode``. If ``unicode``, 
        encoded to utf-8 ``bytes``

.. py:function::    socket.send(self, object obj, flags=0, copy=True)

        `obj` is ``bytes`` or provides buffer interface. 
        
        if `obj` is ``unicode``, raise ``TypeError``

.. py:function::    socket.recv(self, flags=0, copy=True)

        returns ``bytes`` if `copy=True`
        
        returns ``zmq.Message`` if `copy=False`:
        
            `message.buffer` is a buffer view of the ``bytes``
            
            `str(message)` provides the ``bytes``
            
            `unicode(message)` decodes `message.buffer` with utf-8
    
.. py:function::    socket.send_string(self, unicode s, flags=0, encoding='utf-8')

        takes a ``unicode`` string `s`, and sends the ``bytes`` 
        after encoding without an extra copy, via:
        
        `socket.send(s.encode(encoding), flags, copy=False)`
    
.. py:function::    socket.recv_string(self, flags=0, encoding='utf-8')

        always returns ``unicode`` string
        
        there will be a ``UnicodeError`` if it cannot decode the buffer
        
        performs non-copying `recv`, and decodes the buffer with `encoding`
    
.. py:function::    socket.setsockopt(self, opt, optval)

        only accepts ``bytes``  for `optval` (or ``int``, depending on `opt`)
        
        ``TypeError`` if ``unicode`` or anything else
    
.. py:function::    socket.getsockopt(self, opt)

        returns ``bytes`` (or ``int``), never ``unicode``
    
.. py:function::    socket.setsockopt_string(self, opt, unicode optval, encoding='utf-8')

        accepts ``unicode`` string for `optval`
        
        encodes `optval` with `encoding` before passing the ``bytes`` to 
        `setsockopt`
    
.. py:function::    socket.getsockopt_string(self, opt, encoding='utf-8')

        always returns ``unicode`` string, after decoding with `encoding`
        
        note that `zmq.IDENTITY` is the only `sockopt` with a string value 
        that can be queried with `getsockopt`

