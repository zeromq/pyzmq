.. _draft:

Working with libzmq DRAFT sockets
=================================

libzmq-4.2 has introduced the concept of unstable DRAFT APIs.
As of libzmq-4.2, this includes the CLIENT-SERVER and RADIO-DISH patterns.

Because these APIs are explicitly unstable,
pyzmq does not support them by default,
and pyzmq binaries (wheels) will not be built with DRAFT API support.
However, pyzmq-17 can be built with draft socket support,
as long as you compile pyzmq yourself with a special flag.

To install libzmq with draft support:

.. sourcecode:: bash

    ZMQ_VERSION=4.3.4
    PREFIX=/usr/local

    wget https://github.com/zeromq/libzmq/releases/download/v${ZMQ_VERSION}/zeromq-${ZMQ_VERSION}.tar.gz -O libzmq.tar.gz
    tar -xzf libzmq.tar.gz
    cd zeromq-${ZMQ_VERSION}
    ./configure --prefix=${PREFIX} --enable-drafts
    make -j && make install


And to install pyzmq with draft support:

.. sourcecode:: bash

    export ZMQ_PREFIX=${PREFIX}
    export ZMQ_DRAFT_API=1
    pip install -v --no-binary pyzmq --pre pyzmq

By specifying ``--no-binary pyzmq``, pip knows to not install wheels, and will compile pyzmq from source.

The ``ZMQ_PREFIX=$PREFIX`` part is only necessary if libzmq is installed somewhere not on the default search path.
If libzmq is installed in :file:`/usr/local` or similar,
only the ``ZMQ_ENABLE_DRAFTS`` option is required.

There are examples of the CLIENT-SERVER and RADIO-DISH patterns in the :file:`examples/draft`
directory of the pyzmq repository.
