==============================
PyZMQ: Python bindings for 0MQ
==============================

This package contains Python bindings for `0QM <http://www.zeromq.org>`_.
0MQ is a lightweight and fast messaging implementation.

Building and installation
=========================

General
-------

To build and install this Python package, you will first need to build and
install the latest development version of 0MQ itself. After you have done
this, follow these steps:

First, copy the ``setup.cfg.template`` file in this directory to ``setup.cfg``
and edit the `include_dirs` and `library_dirs` fields of the ``setup.cfg``
file to point to the directories that contain the library and header file for
your 0MQ installation.

Second, run this command::

    $ python setup.py install

Cython is not required to build pyzmq, but it is required if you want to
develop pyzmq.

Windows
-------

Generally you'll need to add the location of ``libzmq.dll`` to your ``$PATH``.
Here's Microsoft's docs:
http://msdn.microsoft.com/en-us/library/7d83bc18(VS.80).aspx on this topic.

It is best to compile both ØMQ and PyØMQ with Microsoft Visual Studio 2008 or
above. You should not need to use mingw.

Linux
-----

On Linux, you will need to do one of the following:

* Set ``LD_LIBRARY_PATH`` to point to the :file:`lib` directory of 0MQ.
* Build the extension using the ``-rpath`` flag::

    $ python setup.py build_ext --rpath=/opt/zeromq-dev/lib --inplace

Development
-----------

If you want to develop this package, instead of ``python setup.py install``
do::

    $ python setup.py build_ext --inplace
    $ python setupegg.py develop

This will build the C extension inplace and then put this directory on your
``sys.path``. With this configuration you only have to run::

    $ python setup.py build_ext --inplace

each time you change the ``.pyx`` files. To clean the sources, you can do::

    $ python setup.py clean

Testing
-------

To run the test suite after installing, just do::

    $ python setup.py test

Authors
=======

This project was started by Brian E. Granger (ellisonbg AT gmail DOT com).

The following people have contributed to the project:

* Carlos Rocha (carlos DOT rocha AT gmail DOT com)
* Andrew Gwozdziewycz (git AT apgwoz DOT com)
* Fernando Perez (fernando DOT perez AT berkeley DOT edu)
* Nicholas Piel (nicholas AT nichol DOT as)
