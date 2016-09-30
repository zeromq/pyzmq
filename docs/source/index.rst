.. PyZMQ documentation master file, created by
   sphinx-quickstart on Sat Feb 20 23:31:19 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyZMQ Documentation
===================

:Release: |release|
:Date: |today|


PyZMQ is the Python bindings for ØMQ_.
This documentation currently contains notes on some important aspects of developing PyZMQ and
an overview of what the ØMQ API looks like in Python. For information on how to use
ØMQ in general, see the many examples in the excellent `ØMQ Guide`_, all of which
have a version in Python.

PyZMQ works with Python 3 (≥ 3.3), and Python 2.7, with no transformations or 2to3,
as well as PyPy (at least 2.0 beta), via CFFI.

Please don't hesitate to report pyzmq-specific issues to our tracker_ on GitHub.
General questions about ØMQ are better sent to the `ØMQ tracker`_ or `mailing list`_.

:doc:`changelog`


Supported LibZMQ
================

PyZMQ aims to support all stable ( ≥2.1.4, ≥ 3.2.2, ≥ 4.0.1 ) and active development ( ≥ 4.2.0 )
versions of libzmq.  Building the same pyzmq against various versions of libzmq is supported,
but only the functionality of the linked libzmq will be available.

.. note::

    libzmq 3.0-3.1 are not, and will never be supported.
    There never was a stable release of either.


Binary distributions (wheels on `PyPI <http://pypi.python.org/pypi/pyzmq>`__
or `GitHub <https://www.github.com/zeromq/pyzmq/downloads>`__) of PyZMQ ship with
the stable version of libzmq at the time of release, built with default configuration,
and include CURVE support provided by tweetnacl.
For pyzmq-|release|, this is |target_libzmq|.

Using PyZMQ
===========

.. toctree::
    :maxdepth: 2
    
    api/index.rst
    changelog.rst
    morethanbindings.rst
    serialization.rst
    devices.rst
    eventloop.rst
    logging.rst
    ssh.rst
    

Notes from developing PyZMQ
===========================

.. toctree::
    :maxdepth: 2
    
    pyversions.rst
    unicode.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Links
=====

* ØMQ_ Home
* The `ØMQ Guide`_
* `PyZMQ Installation`_ notes on the ZeroMQ website
* PyZMQ on GitHub_
* Issue Tracker_

.. _ØMQ: http://www.zeromq.org
.. _ØMQ Guide: http://zguide.zeromq.org
.. _ØMQ Tracker: https://github.com/zeromq/libzmq/issues
.. _mailing list: http://www.zeromq.org/docs:mailing-lists
.. _IRC Channel: http://www.zeromq.org/chatroom
.. _Cython: http://cython.org/
.. _GitHub: https://www.github.com/zeromq/pyzmq
.. _ØMQ Manual: http://www.zeromq.org/intro:read-the-manual
.. _PyZMQ Installation: http://www.zeromq.org/bindings:python
.. _tracker: https://www.github.com/zeromq/pyzmq/issues

