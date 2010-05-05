==============================
PyZMQ: Python bindings for 0MQ
==============================

This package contains Python bindings for `0QM <http://www.zeromq.org>`_.
0MQ is a lightweight and fast messaging implementation.

Building and installation
=========================

To build and install this Python package, you will first need to build and
install the latest development version of 0MQ itself. After you have done
this, follow these steps:

First, copy the ``setup.cfg.template`` file in this directory to ``setup.cfg``
and edit the `include_dirs` and `library_dirs` fields of the ``setup.cfg``
file to point to the directories that contain the library and header file for
your 0MQ installation.

Cython is not required to build pyzmq, but it is required if you
want to develop pyzmq.

On Windows, it is easiest to simply copy ``libzmq.dll`` and ``zmq.h``
into the ``zmq`` subdirectory and set ``library_dirs`` to ``.\zmq``.

Second, run this command::

    python setup.py install

If you want to develop this package, instead of this last command do::

    python setup.py build_ext --inplace
    python setupegg.py develop

This will build the C extension inplace and then put this directory on your
``sys.path``. With this setup you only have to run::

    python setup.py build_ext --inplace

each time you change the ``.pyx`` files.

Authors
=======

This project was started by Brian E. Granger (ellisonbg AT gmail DOT com).

The following people have contributed to the project:

* Carlos Rocha (carlos DOT rocha AT gmail DOT com)
* Andrew Gwozdziewycz (git AT apgwoz DOT com)
* Fernando Perez (fernando DOT perez AT berkeley DOT edu)
* Nicholas Piel (nicholas AT nichol DOT as)
