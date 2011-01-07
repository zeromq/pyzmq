.. PyZMQ Version compatibility doc, by Min Ragan-Kelley, 2010

.. _pyversions:

PyZMQ, Python2.5, and Python3
=============================

PyZMQ is a fairly light, low-level library, so supporting as many versions
as is reasonable is our goal.  Currently, we support at least Python 2.5-3.1.
Making the changes to the codebase required a few tricks, which are documented here
for future reference, either by us or by other developers looking to support several
versions of Python.

.. Note::

    It is far simpler to support 2.6-3.x than to include 2.5. Many of the significant
    syntax changes have been backported to 2.6, so just writing new-style code would work
    in many cases. I will try to note these points as they come up.


pyversion_compat.h
------------------

Many functions we use, primarily involved in converting between C-buffers and Python
objects, are not available on all supported versions of Python. In order to resolve
missing symbols, we added a header :file:`utils/pyversion_compat.h` that defines missing
symbols with macros. Some of these macros alias new names to old functions (e.g.
``PyBytes_AsString``), so that we can call new-style functions on older versions, and some
simply define the function as an empty exception raiser. The important thing is that the
symbols are defined to prevent compiler warnings and linking errors. Everywhere we use
C-API functions that may not be available in a supported version, at the top of the file
is the code:

.. sourcecode:: guess

    cdef extern from "pyversion_compat.h":
        pass

This ensures that the symbols are defined in the Cython generated C-code. Higher level
switching logic exists in the code itself, to prevent actually calling unavailable
functions, but the symbols must still be defined.

Bytes and Strings
-----------------

.. Note::

    If you are using Python >= 2.6, to prepare your PyZMQ code for Python3 you should use
    the ``b'message'`` syntax to ensure all your string literal messages will still be
    :class:`bytes` after you make the upgrade.

The most cumbersome part of PyZMQ compatibility from a user's perspective is the fact
that, since ØMQ uses C-strings, and would like to do so without copying, we must use the
Py3k :class:`bytes` object, which is backported to 2.6. In order to do this in a
Python-version independent way, we added a small utility that unambiguously defines the
string types: :class:`bytes`, :class:`unicode`, :obj:`basestring`. This is important,
because :class:`str` means different things on 2.x and 3.x, and :class:`bytes` is
undefined on 2.5, and both :class:`unicode` and :obj:`basestring` are undefined on 3.x.
All typechecking in PyZMQ is done against these types:

=================  =================   ====================
Explicit Type           2.x                      3.x
=================  =================   ====================
:obj:`bytes`       :obj:`str`          :obj:`bytes`
:obj:`unicode`     :obj:`unicode`      :obj:`str`
:obj:`basestring`  :obj:`basestring`   :obj:`(str, bytes)`
=================  =================   ====================

.. Note::
    
    2.5 specific

    Where we really noticed the issue of :class:`bytes` vs :obj:`strings` coming up for
    users was in updating the tests to run on every version. Since the ``b'bytes
    literal'`` syntax was not backported to 2.5, we must call ``"message".encode()`` for
    *every* string in the test suite.

.. seealso:: :ref:`Unicode discussion <unicode>` for more information on strings/bytes.

``PyBytes_*``
*************

The standard C-API function for turning a C-string into a Python string was a set of
functions with the prefix ``PyString_*``. However, with the Unicode changes made in
Python3, this was broken into ``PyBytes_*`` for bytes objects and ``PyUnicode_*`` for
unicode objects. We changed all our ``PyString_*`` code to ``PyBytes_*``, which was
backported to 2.6.


.. Note::

    2.5 Specific:

    Since Python 2.5 doesn't support the ``PyBytes_*`` functions, we had to alias them to
    the ``PyString_*`` methods in utils/pyversion_compat.h.

    .. sourcecode:: c++

        #define PyBytes_FromStringAndSize PyString_FromStringAndSize
        #define PyBytes_FromString PyString_FromString
        #define PyBytes_AsString PyString_AsString
        #define PyBytes_Size PyString_Size

Buffers
-------

The layer that is most complicated for developers, but shouldn't trouble users, is the
Python C-Buffer APIs. These are the methods for converting between Python objects and C
buffers. The reason it is complicated is that it keeps changing.

There are two buffer interfaces for converting an object to a C-buffer, known as new-style
and old-style. Old-style buffers were introduced long ago, but the new-style is only
backported to 2.6. The old-style buffer interface is not available in 3.x. There is also
an old- and new-style interface for creating Python objects that view C-memory. The
old-style object is called a :class:`buffer`, and the new-style object is
:class:`memoryview`. Unlike the new-style buffer interface for objects,
:class:`memoryview` has only been backported to *2.7*. This means that the available
buffer-related functions are not the same in any two versions of Python 2.5, 2.6, 2.7, or
3.1.

We have a :file:`utils/buffers.pxd` file that defines our :func:`asbuffer` and
:func:`frombuffer` functions. :file:`utils/buffers.pxd` was adapted from mpi4py_'s
:file:`asbuffer.pxi`. The :func:`frombuffer` functionality was added. These functions
internally switch based on Python version to call the appropriate C-API functions.

.. seealso:: `Python Buffer API <bufferapi>`_

.. _bufferapi: http://docs.python.org/c-api/buffer.html


``__str__``
-----------

As discussed, :class:`str` is not a platform independent type. The two places where we are
required to return native str objects are :func:`error.strerror`, and
:func:`Message.__str__`. In both of these cases, the natural return is actually a
:class:`bytes` object. In the methods, the native :class:`str` type is checked, and if the
native str is actually unicode, then we decode the bytes into unicode:

.. sourcecode:: py

    # ...
    b = natural_result()
    if str is unicode:
        return b.decode()
    else:
        return b

Exceptions
----------

.. Note::

    This section is only relevant for supporting Python 2.5 and 3.x, not for 2.6-3.x.

The syntax for handling exceptions has `changed <PEP-3110>`_ in Python 3.  The old syntax:

.. sourcecode:: py

    try:
        s.send(msg)
    except zmq.ZMQError, e:
        handle(e)

is no longer valid in Python 3. Instead, the new syntax for this is:

.. sourcecode:: py

    try:
        s.send(msg)
    except zmq.ZMQError as e:
        handle(e)

This new syntax is backported to Python 2.6, but is invalid on 2.5. For 2.6-3.x compatible
code, we could just use the new syntax. However, the only method we found to catch an
exception for handling on both 2.5 and 3.1 is to get the exception object inside the
exception block:

.. sourcecode:: py

    try:
        s.send(msg)
    except zmq.ZMQError:
        e = sys.exc_info()[1]
        handle(e)

This is certainly not as elegant as either the old or new syntax, but it's the only way we
have found to work everywhere.

.. seealso:: PEP-3110_

.. _PEP-3110: http://www.python.org/dev/peps/pep-3110/


.. _mpi4py: http://mpi4py.googlecode.com