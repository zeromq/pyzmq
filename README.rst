==============================
PyZMQ: Python bindings for ØMQ
==============================

This package contains Python bindings for `ØMQ <http://www.zeromq.org>`_.
ØMQ is a lightweight and fast messaging implementation.

PyZMQ should work with libzmq ≥ 2.1.4 (including libzmq 3.2.x), and Python ≥ 2.6 (including Python 3).

Versioning
==========

Current release of pyzmq is 2.2.0, and targets libzmq-2.2.0. For libzmq
2.0.x, use pyzmq release 2.0.10.1 or the 2.0.x development branch.

pyzmq-2.1.11 was the last version of pyzmq to support Python 2.5, and pyzmq 2.2.0 will
require Python ≥ 2.6.

PyZMQ versioning follows libzmq versioning. In general, your pyzmq version should be the same
as that of your libzmq, but due to the generally growing API of libzmq, your pyzmq should
*not* be newer than your libzmq. This is a strict restriction for pyzmq <= 2.1.0, but we
intend to support libzmq >= 2.1.4 (the first 'stable' 2.1 release) for pyzmq 2.1.x.

For a summary of changes to pyzmq, see our `changelog <http://zeromq.github.com/pyzmq/changelog.html>`_.

ØMQ 3.x
-------

As of 2.1.7, we have experimental support for the 3.x API of libzmq,
developed at https://github.com/zeromq/libzmq. No code to change, no flags to pass, just
build pyzmq against libzmq3 and it should work.

Documentation
=============

See PyZMQ's Sphinx-generated `documentation <http://zeromq.github.com/pyzmq>`_ on GitHub for API
details, and some notes on Python and Cython development.  If you want to learn about
using ØMQ in general, the excellect `ØMQ Guide <http://zguide.zeromq.org>`_ is the place
to start, which has a Python version of every example.

Downloading
===========

Unless you specifically want to develop PyZMQ, we recommend downloading the
PyZMQ source code or MSI installer from our `GitHub download page <https://github.com/zeromq/pyzmq/downloads>`_,
or an egg from `PyPI <http://pypi.python.org/pypi/pyzmq>`_.

You can also get the latest source code from our GitHub repository, but
building from the repository will require that you install Cython version 0.13
or later.


Building and installation
=========================

pip
---

We build eggs for OS X and Windows, so we recommend that those platforms use ``easy_install pyzmq``.
But many users prefer pip, which unfortunately still ignores eggs.
In an effort to make pyzmq easier to install,
pyzmq will try to build libzmq as a Python extension if it cannot find a libzmq to link against.

This is thanks to work done in `pyzmq_static <https://github.com/brandon-rhodes/pyzmq-static>`_.

Linking against system libzmq is still the preferred mechanism,
so pyzmq will try pretty hard to find it.
You can skip the searching by explicitly specifying that pyzmq build its own libzmq::

    $> pip install pyzmq --install-option="--zmq=bundled"


Eggs and MSIs
-------------

We have binary installers for various Pythons on OSX and Windows, so you should be able to
just ``easy_install pyzmq`` in many situations. These eggs *include matching libzmq*, so they should
be the only thing you need to start using pyzmq, but we simply don't have the experience to know
when and where these installers will not work.

If a binary installer fails for you, please `tell us <https://github.com/zeromq/pyzmq/issues>`_
about your system and the failure, so that we can try to fix it in later releases, and fall back
on building from source.

Eggs are on `PyPI <http://pypi.python.org/pypi/pyzmq>`_, and we have them for 'current' Pythons,
which are for OSX 10.7:

  * Python 2.7, 3.2 (32b+64b intel)
  
and OSX 10.6:

  * Python 2.6 (32b+64b intel)

and Windows (x86 and x64):

  * Python 2.7, 3.2

We also have MSI installer packages in our `downloads
<http://github.com/zeromq/pyzmq/downloads>`_ section on GitHub.

A Python 2.6/win64 MSI for 2.1.7 was provided by Craig Austin (craig DOT austin AT gmail DOT com)

Our build scripts are much improved as of 2.1.4, so if you would like to contribute better
Windows installers, or have any improvements on existing releases, they would be much
appreciated. Simply ``python setup.py bdist_msi`` or ``python setupegg.py bdist_egg`` *should*
work, once you have libzmq and Python. We simply don't have the VMs or time in which to cover
all the bases ourselves.

.. note::
    Sometimes libzmq.so/dll/dylib doesn't get included unless ``build`` is
    specified *also*, e.g. ``python setupegg.py build bdist_egg``, but this
    doesn't always seem to be true.

General
-------

To build and install pyzmq from source, you will first need to build libzmq. 
After you have done this, follow these steps:

Tell pyzmq where libzmq is via the configure subcommand:

    $ python setup.py configure --zmq=/path/to/zeromq

or the zmq install directory on OSX/Linux:

    $ python setup.py configure --zmq=/usr/local

The argument should be a directory containing ``lib`` and ``include`` directories, with
``libzmq`` and ``zmq.h`` respectively. For instance (on Windows), if you have downloaded pyzmq
and current libzmq into the same parent directory, this would be:

    $ python setup.py configure --zmq=../zeromq-2.2.0

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

Windows x64
***********

64b Windows builds have been successful (as of 2.1.7.1), using VC++ 2008 express, and the
Windows 7 SDK. VS2008 had to be patched as described `here
<http://www.cppblog.com/xcpp/archive/2009/09/09/vc2008express_64bit_win7sdk.html>`_, and
pyzmq was built following `these instructions <http://wiki.cython.org/64BitCythonExtensionsOnWindows>`_ on the Cython wiki.

Linux
-----

If you install libzmq to a location other than the default (``/usr/local``) on Linux,
you may need to do one of the following:

* Set ``LD_LIBRARY_PATH`` to point to the ``lib`` directory of ØMQ.
* Build the extension using the ``--rpath`` flag::

    $ python setup.py build_ext --rpath=/opt/zeromq-dev/lib --inplace

Mac OSX
-------

The easiest way to install libzmq on OSX is with the wonderful `homebrew <http://mxcl.github.com/homebrew/>`_
package manager, via::

    $ brew install zeromq

And to build a 32+64b intel fat binary, add ``--universal``::

    $ brew install zeromq --universal

This will install libzmq in /usr/local, making pyzmq installable with pip, which doesn't
support our binary eggs.

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

* Check the version number in ``version.py``.
* Remove old ``MANIFEST`` and ``egg-info`` files and ``dist`` and ``build``
  directories.
* Check ``MANIFEST.in``.
* Register the release with pypi::

    python setup.py register

* Build source distributions and upload::

    python setup.py sdist --formats=zip,gztar upload

* Branch the release (do *not* push the branch)::

    git checkout -b 2.1.9 master

* commit the changed ``version.py`` to the branch::

    git add zmq/core/version.pyx && git commit -m "bump version to 2.1.9"

* Tag the release::

    git tag -a -m "Tagging release 2.1.9" v2.1.9
    git push origin --tags

* Make sure the ``README.rst`` has an updated list of contributors.
* Announce on list.

Authors
=======

This project was started and continues to be led by Brian E. Granger
(ellisonbg AT gmail DOT com).  Min Ragan-Kelley (benjaminrk AT gmail DOT com)
is the primary developer of pyzmq at this time.

The following people have contributed to the project:


* Andrea Crotti (andrea DOT crotti DOT 0 AT gmail DOT com)
* Andrew Gwozdziewycz (git AT apgwoz DOT com)
* Baptiste Lepilleur (baptiste DOT lepilleur AT gmail DOT com)
* Brandyn A. White (bwhite AT dappervision DOT com)
* Brian E. Granger (ellisonbg AT gmail DOT com)
* Carlos A. Rocha (carlos DOT rocha AT gmail DOT com)
* Daniel Lundin (dln AT spotify DOT com)
* Daniel Truemper (truemped AT googlemail DOT com)
* Erick Tryzelaar (erick DOT tryzelaar AT gmail DOT com)
* Erik Tollerud (erik DOT tollerud AT gmail DOT com)
* Fernando Perez (Fernando DOT Perez AT berkeley DOT edu)
* Frank Wiles (frank AT revsys DOT com)
* Gavrie Philipson (gavriep AT il DOT ibm DOT com)
* Godefroid Chapelle (gotcha AT bubblenet DOT be)
* Ivo Danihelka (ivo AT danihelka DOT net)
* John Gallagher (johnkgallagher AT gmail DOT com)
* Justin Riley (justin DOT t DOT riley AT gmail DOT com)
* Marc Abramowitz (marc AT marc-abramowitz DOT com)
* Michel Pelletier (pelletier DOT michel AT gmail DOT com)
* Min Ragan-Kelley (benjaminrk AT gmail DOT com)
* Nicholas Piël (nicholas AT nichol DOT as)
* Nick Pellegrino (npellegrino AT mozilla DOT com)
* Ondrej Certik (ondrej AT certik DOT cz)
* Paul Colomiets (paul AT colomiets DOT name)
* Scott Sadler (github AT mashi DOT org)
* Stefan Friesel (sf AT cloudcontrol DOT de)
* Stefan van der Walt (stefan AT sun DOT ac DOT za)
* Thomas Kluyver (takowl AT gmail DOT com)
* Thomas Spura (tomspur AT fedoraproject DOT org)
* Tigger Bear (Tigger AT Tiggers-Mac-mini DOT local)
* Zbigniew Jędrzejewski-Szmek (zbyszek AT in DOT waw DOT pl)
* hugo  shi (hugoshi AT bleb2 DOT (none))
* spez (steve AT hipmunk DOT com)

as reported by::

    git log --all --format='* %aN (%aE)' | sort -u | sed 's/@/ AT /1' | sed -e 's/\./ DOT /g'

with some adjustments.

Not in git log
--------------

* Brandon Craig-Rhodes (brandon AT rhodesmill DOT org)
* Eugene Chernyshov (chernyshov DOT eugene AT gmail DOT com)
* Douglas Creager (dcreager AT dcreager DOT net)
* Craig Austin (craig DOT austin AT gmail DOT com)


gevent_zeromq, now zmq.green
----------------------------

* Travis Cline (travis DOT cline AT gmail DOT com)
* Ryan Kelly (ryan AT rfk DOT id DOT au)
* Zachary Voase (z AT zacharyvoase DOT com)


