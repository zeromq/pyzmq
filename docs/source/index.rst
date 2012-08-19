.. PyZMQ documentation master file, created by
   sphinx-quickstart on Sat Feb 20 23:31:19 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyZMQ Documentation
===================
.. htmlonly::

   :Release: |release|
   :Date: |today|


PyZMQ is the Python bindings for ØMQ_, written almost entirely in Cython_. This
documentation currently contains notes on some important aspects of developing PyZMQ and
an overview of what the ØMQ API looks like in Python. For information on how to use
ØMQ in general, see the many examples in the excellent `ØMQ Guide`_, all of which
have a version in Python.

PyZMQ works with Python 3 (≥ 3.2), and Python 2 (≥ 2.6), with no transformations or 2to3,
largely thanks to Cython_.

Please don't hesitate to report pyzmq-specific issues to our tracker_ on GitHub.
General questions about ØMQ are better sent to the ØMQ `mailing list`_ or `IRC Channel`_.

:ref:`Summary of Changes in PyZMQ <changelog>`


PyZMQ Versioning
================

PyZMQ versioning follows libzmq, so your pyzmq version should match that of your
libzmq. Building the same pyzmq against various versions of libzmq is supported,
and should only result in the addition/removal of a few socket types and socket
options, depending on the active libzmq's support.

Binary distributions (eggs or MSIs on `PyPI <http://pypi.python.org/pypi/pyzmq>`__
or `GitHub <https://www.github.com/zeromq/pyzmq/downloads>`__) of PyZMQ ship with
matching libzmq release built with default configuration.

PyZMQ aims to support all stable ( ≥2.1.4 ) and active development ( ≥3.2.0 )
versions of libzmq.


Notes from developing PyZMQ
===========================

.. toctree::
    :maxdepth: 2
    
    pyversions.rst
    unicode.rst

Using PyZMQ
===========

.. toctree::
    :maxdepth: 2
    
    morethanbindings.rst
    serialization.rst
    devices.rst
    eventloop.rst
    logging.rst
    ssh.rst
    
    api/index.rst

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
.. _mailing list: http://www.zeromq.org/docs:mailing-lists
.. _IRC Channel: http://www.zeromq.org/chatroom
.. _Cython: http://cython.org/
.. _GitHub: https://www.github.com/zeromq/pyzmq
.. _ØMQ Manual: http://www.zeromq.org/intro:read-the-manual
.. _PyZMQ Installation: http://www.zeromq.org/bindings:python
.. _tracker: https://www.github.com/zeromq/pyzmq/issues

