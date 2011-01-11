.. PyZMQ documentation master file, created by
   sphinx-quickstart on Sat Feb 20 23:31:19 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyZMQ Documentation
===================
.. htmlonly::

   :Release: |release|
   :Date: |today|

.. Note::

    These docs are for pyzmq-|release|, but pyzmq has not made any significant changes to
    itself since 2.0.10, so they should apply just fine there as well.
    
    PyZMQ versioning follows zeromq, so your pyzmq version should match those of your
    zeromq. The only changes at the pyzmq user's level are the addition of a few socket
    types and socket options.

PyZMQ is the Python bindings for ØMQ_, written almost entirely in Cython_. This
documentation currently contains notes on some important aspects of developing PyZMQ and
an overview of what the ØMQ API looks like in Python. For information on how to use
ØMQ in general, see the excellent `ØMQ Manual`_.

Please don't hesitate to report pyzmq issues to our tracker_ on GitHub.

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
   devices.rst
   eventloop.rst
   logging.rst
   api/index.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Links
=====

* ØMQ_ Home
* `PyZMQ Installation`_ notes on the ZeroMQ website
* PyZMQ on GitHub_
* Issue Tracker_

.. _ØMQ: http://www.zeromq.org
.. _Cython: http://cython.org/
.. _GitHub: https://www.github.com/zeromq/pyzmq
.. _ØMQ Manual: http://www.zeromq.org/intro:read-the-manual
.. _PyZMQ Installation: http://www.zeromq.org/bindings:python
.. _tracker: https://www.github.com/zeromq/pyzmq/issues

