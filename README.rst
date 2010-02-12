=======================
Python bindings for 0MQ
=======================

This package contains Python bindings for `0QM <http://www.zeromq.org>`_.
0MQ is lightweight and fast messaging implementation.

Building and installation
=========================

To build and install this Python package, you will first need to build
and install 0MQ itself. After you have done this, follow these steps:

First, edit the `include_dirs` and `library_dirs` fields of the
``setup.cfg`` file in this directory to point to the directories that
contain the library and header file for your 0MQ installation.

Second, run this command::

    python setup.py install

If you want to develop this package, instead of this last command do::

    python setup.py build_ext --inplace
    python setupegg.py develop

This will build the C extension inplace and then put this directory on your
``sys.path``. With this setup you only have to run::

    python setup.py build_ext --inplace

each time you change the ``.pyx`` files.

Todo
====

* Test on Windows.
* Write examples and tests.
* Implement poll.
