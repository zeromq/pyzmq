# PyZMQ: Python bindings for ØMQ


This package contains Python bindings for [ØMQ](http://www.zeromq.org).
ØMQ is a lightweight and fast messaging implementation.

PyZMQ should work with libzmq ≥ 2.1.4 (including libzmq 3.2.x), and
Python ≥ 2.6 (including Python 3).

## Versioning

Current release of pyzmq is 2.2.0.1, and targets libzmq-2.2.0. For
libzmq 2.0.x, use pyzmq release 2.0.10.1 or the 2.0.x development
branch.

pyzmq-2.1.11 was the last version of pyzmq to support Python 2.5, and
pyzmq ≥ 2.2.0 requires Python ≥ 2.6.

PyZMQ releases ≤ 2.2.0 matched libzmq versioning, but this will no
longer be the case. To avoid confusion with the contemporary libzmq-3.2
major version release, PyZMQ is jumping to 13.0 (it will be the
thirteenth release, so why not?). PyZMQ ≥ 13.0 will follow semantic
versioning conventions accounting only for PyZMQ itself.

For a summary of changes to pyzmq, see our
[changelog](http://zeromq.github.com/pyzmq/changelog.html).

### ØMQ 3.x

PyZMQ ≥ 2.2.0 fully supports the 3.x API of libzmq,
developed at [zeromq/libzmq](https://github.com/zeromq/libzmq).
No code to change, no flags to pass,
just build pyzmq against libzmq3 and it should work.

## Documentation

See PyZMQ's Sphinx-generated
[documentation](http://zeromq.github.com/pyzmq) on GitHub for API
details, and some notes on Python and Cython development. If you want to
learn about using ØMQ in general, the excellent [ØMQ
Guide](http://zguide.zeromq.org) is the place to start, which has a
Python version of every example. We also have some information on our
[wiki](https://github.com/zeromq/pyzmq/wiki)

## Downloading

Unless you specifically want to develop PyZMQ, we recommend downloading
the PyZMQ source code, eggs, or MSI installer from
[PyPI](http://pypi.python.org/pypi/pyzmq).

You can also get the latest source code from our GitHub repository, but
building from the repository will require that you install Cython
version 0.15 or later.

## Building and installation

For more detail on building pyzmq, see [our Wiki](https://github.com/zeromq/pyzmq/wiki).

We build eggs for OS X and Windows, so we generally recommend that those
platforms use `easy_install pyzmq`, but `pip install pyzmq` should on
most platforms as well.

To build pyzmq from the git repo requires Cython.

## Authors

This project was started and continues to be led by Brian E. Granger
(ellisonbg AT gmail DOT com). Min Ragan-Kelley (benjaminrk AT gmail DOT
com) is the primary developer of pyzmq at this time.

The following people have contributed to the project:

-   Andrea Crotti (andrea DOT crotti DOT 0 AT gmail DOT com)
-   Andrew Gwozdziewycz (git AT apgwoz DOT com)
-   Baptiste Lepilleur (baptiste DOT lepilleur AT gmail DOT com)
-   Brandyn A. White (bwhite AT dappervision DOT com)
-   Brian E. Granger (ellisonbg AT gmail DOT com)
-   Carlos A. Rocha (carlos DOT rocha AT gmail DOT com)
-   Daniel Lundin (dln AT spotify DOT com)
-   Daniel Truemper (truemped AT googlemail DOT com)
-   Erick Tryzelaar (erick DOT tryzelaar AT gmail DOT com)
-   Erik Tollerud (erik DOT tollerud AT gmail DOT com)
-   Fernando Perez (Fernando DOT Perez AT berkeley DOT edu)
-   Frank Wiles (frank AT revsys DOT com)
-   Gavrie Philipson (gavriep AT il DOT ibm DOT com)
-   Godefroid Chapelle (gotcha AT bubblenet DOT be)
-   Ivo Danihelka (ivo AT danihelka DOT net)
-   John Gallagher (johnkgallagher AT gmail DOT com)
-   Justin Riley (justin DOT t DOT riley AT gmail DOT com)
-   Marc Abramowitz (marc AT marc-abramowitz DOT com)
-   Michel Pelletier (pelletier DOT michel AT gmail DOT com)
-   Min Ragan-Kelley (benjaminrk AT gmail DOT com)
-   Nicholas Piël (nicholas AT nichol DOT as)
-   Nick Pellegrino (npellegrino AT mozilla DOT com)
-   Ondrej Certik (ondrej AT certik DOT cz)
-   Paul Colomiets (paul AT colomiets DOT name)
-   Scott Sadler (github AT mashi DOT org)
-   Stefan Friesel (sf AT cloudcontrol DOT de)
-   Stefan van der Walt (stefan AT sun DOT ac DOT za)
-   Thomas Kluyver (takowl AT gmail DOT com)
-   Thomas Spura (tomspur AT fedoraproject DOT org)
-   Tigger Bear (Tigger AT Tiggers-Mac-mini DOT local)
-   Zbigniew Jędrzejewski-Szmek (zbyszek AT in DOT waw DOT pl)
-   hugo shi (hugoshi AT bleb2 DOT (none))
-   spez (steve AT hipmunk DOT com)

as reported by:

    git log --all --format='* %aN (%aE)' | sort -u | sed 's/@/ AT /1' | sed -e 's/\./ DOT /g'

with some adjustments.

### Not in git log

-   Brandon Craig-Rhodes (brandon AT rhodesmill DOT org)
-   Eugene Chernyshov (chernyshov DOT eugene AT gmail DOT com)
-   Douglas Creager (dcreager AT dcreager DOT net)
-   Craig Austin (craig DOT austin AT gmail DOT com)

### gevent\_zeromq, now zmq.green

-   Travis Cline (travis DOT cline AT gmail DOT com)
-   Ryan Kelly (ryan AT rfk DOT id DOT au)
-   Zachary Voase (z AT zacharyvoase DOT com)

