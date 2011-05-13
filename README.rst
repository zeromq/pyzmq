==============================
PyZMQ: Python bindings for ØMQ
==============================

This package contains Python bindings for `ØMQ <http://www.zeromq.org>`_.
ØMQ is a lightweight and fast messaging implementation.

Versioning
==========

Current release of pyzmq is 2.1.7, and targets libzmq-2.1.7. For libzmq
2.0.x, use pyzmq release 2.0.10.1 or the 2.0.x development branch.

PyZMQ versioning follows libzmq versioning. In general, your pyzmq version should be the same
as that of your libzmq, but due to the generally growing API of libzmq, your pyzmq should
*not* be newer than your libzmq. This is a strict restriction for pyzmq <= 2.1.0, but we
intend to support libzmq >= 2.1.0 for pyzmq 2.1.x.

ØMQ 3.0
-------

As of 2.1.7, we have experimental support for the 3.0 API of libzmq,
developed at https://github.com/zeromq/libzmq. No code to change, no flags to pass, just
build against libzmq 3 and it should work.  The pyzmq API has not changed.


Documentation
=============

See PyZMQ's Sphinx `generated documentation <http://zeromq.github.com/pyzmq>`_ on GitHub for API
details, and some notes on Python and Cython development.

Downloading
===========

Unless you specifically want to develop PyZMQ, we recommend downloading the
PyZMQ source code from our github download page here:

https://github.com/zeromq/pyzmq/downloads

While you can also get the latest source code by forking our github
repository, building from the repository will require that you download and
install Cython version 0.13 or later.

Building and installation
=========================

Eggs
----

We have binary installers for various Pythons on OSX and (32b) Windows, so you should be able to
just ``easy_install pyzmq`` in many situations. These eggs *include libzmq-2.1.7*, so they should
be the only thing you need to start using pyzmq, but we simply don't have the experience to know
when and where these installers will not work.

If a binary installer fails for you, please `tell us <https://github.com/zeromq/pyzmq/issues>`_
about your system and the failure, so that we can try to fix it in later releases, and fall back
on building from source.

Eggs are on PyPI, and we have them for 'current' Pythons, which are for OSX 10.6:

  * Python 2.6, 2.7, 3.2 (32b and 64b intel)

and win32:

  * Python 2.7, 3.2

We also have MSI installer packages in our `downloads
<http://github.com/zeromq/pyzmq/downloads>`_ section on GitHub.

Our build scripts are much improved as of 2.1.4, so if you would like to contribute 64b Windows
installers, or have any improvements on existing releases, they would be much appreciated.
Simply ``python setup.py bdist_msi`` or ``python setupegg.py bdist_egg`` *should* work, once you
have a 64b libzmq and Python. We simply don't have the VMs or time in which to do this
ourselves.

General
-------

To build and install pyzmq from source, you will first need to build libzmq. 
After you have done this, follow these steps:

Tell pyzmq where libzmq is via the configure subcommand:

    $ python setup.py configure --zmq=/path/to/zeromq2

or the zmq install directory on OSX/Linux:

    $ python setup.py configure --zmq=/usr/local

The argument should be a directory containing a ``lib`` and a ``include`` directory, containing
``libzmq`` and ``zmq.h`` respectively. For instance (on Windows), if you have downloaded pyzmq
and current libzmq into the same parent directory, this would be:

    $ python setup.py configure --zmq=../zeromq-2.1.7

Second, run this command::

    $ python setup.py install

Cython is not required to build pyzmq from a release package, but it is
required if you want to develop pyzmq, or build directly from our repository
on GitHub.

Windows
-------

On Windows, libzmq.dll will be copied into the zmq directory, and installed along with pyzmq,
so you shouldn't need to edit your ``PATH``.

It is best to compile both ØMQ and PyØMQ with Microsoft Visual Studio 2008. You
should not need to use mingw. If you build libzmq with MSVS 2010, then there
will be issues in error handling, because there will be a mismatch between error
numbers.

Current testing indicates that running

    $ python setup.py bdist_msi

successfully builds a working MSI installer, but we don't have enough Windows deployment
experience to know where that may fail.


Linux
-----

If you install libzmq to a location other than the default (``/usr/local``) on Linux,
you may need to do one of the following:

* Set ``LD_LIBRARY_PATH`` to point to the ``lib`` directory of ØMQ.
* Build the extension using the ``--rpath`` flag::

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

* Check the version number in ``version.pyx``.
* Remove old ``MANIFEST`` and ``egg-info`` files and ``dist`` and ``build``
  directories.
* Check ``MANIFEST.in``.
* Register the release with pypi::

    python setup.py register

* Build source distributions and upload::

    python setup.py sdist --formats=zip,gztar upload

* Upload the tarball and ``.zip`` file to github.
* Branch the release::

    git checkout -b 2.1.7 master
    git push origin 2.1.7

* Tag the release::

    git tag -a -m "Tagging release 2.1.7" v2.1.7
    git push origin --tags

* Make sure the ``README.rst`` has an updated list of contributors.
* Announce on list.

Authors
=======

This project was started by and continues to be led by Brian E. Granger
(ellisonbg AT gmail DOT com).

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
* Scott Sadler (github AT mashi DOT org)
* spez (steve AT hipmunk DOT com)
* Thomas Kluyver (takowl AT gmail DOT com)
* Baptiste Lepilleur (baptiste DOT lepilleur AT gmail DOT com)
* Daniel Truemper (truemped AT googlemail DOT com)
