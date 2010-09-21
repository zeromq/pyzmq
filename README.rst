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

* Set ``LD_LIBRARY_PATH`` to point to the ``lib`` directory of 0MQ.
* Build the extension using the ``-rpath`` flag::

    $ python setup.py build_ext --rpath=/opt/zeromq-dev/lib --inplace

Development
-----------

To develop PyZMQ, you will need to install Cython, version 0.13 or greater.
After installing Cython, instead of doing ``python setup.py install`` do::

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

How to release PyZMQ
--------------------

Currently, we are using the following steps to release PyZMQ:

* Change the version number in ``setup.py`` and ``__init__.py``.
* Remove old ``MANIFEST`` and ``egg-info`` files and ``dist`` and ``build``
  directories.
* Check ``MANIFEST.in``.
* Register the release with pypi::

    python setup.py register

* Build source distributions and upload::

    python setup.py sdist --formats=zip,gztar upload

* Upload the tarball and ``.zip`` file to github.
* Branch the release::

    git co -b 2.0.8 master
    git push origin 2.0.8

* Announce on list.

Authors
=======

This project was started by Brian E. Granger (ellisonbg AT gmail DOT com).

The following people have contributed to the project:

* Carlos Rocha (carlos DOT rocha AT gmail DOT com)
* Andrew Gwozdziewycz (git AT apgwoz DOT com)
* Fernando Perez (fernando DOT perez AT berkeley DOT edu)
* Nicholas Piel (nicholas AT nichol DOT as)
* Eugene Chernyshov (chernyshov DOT eugene AT gmail DOT com)
* Justin Riley (justin DOT t DOT riley AT gmail DOT com)
* Ivo Danihelka (ivo AT denihelka DOT net)
* Thomas Supra (tomspur AT fedoraproject DOT org)
* Douglas Creager (dcreager AT dcreager DOT net)
* Erick Tryzelaar (erick DOT tryzelaar AT gmail DOT com)
* Min Ragan-Kelley (benjaminrk AT gmail DOT com)
