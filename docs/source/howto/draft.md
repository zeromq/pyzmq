(draft)=

# Working with libzmq DRAFT sockets

libzmq-4.2 has introduced the concept of unstable DRAFT APIs.
As of libzmq-4.2, this includes the CLIENT-SERVER and RADIO-DISH patterns.

Because these APIs are explicitly unstable,
pyzmq does not support them by default,
and pyzmq binaries (wheels) will not be built with DRAFT API support.
However, pyzmq can be built with draft socket support,
as long as you compile pyzmq yourself with a special flag.

To install libzmq with draft support:

```bash
ZMQ_VERSION=4.3.5
PREFIX=/usr/local
CPU_COUNT=${CPU_COUNT:-$(python3 -c "import os; print(os.cpu_count())")}


wget https://github.com/zeromq/libzmq/releases/download/v${ZMQ_VERSION}/zeromq-${ZMQ_VERSION}.tar.gz -O libzmq.tar.gz
tar -xzf libzmq.tar.gz
cd zeromq-${ZMQ_VERSION}
./configure --prefix=${PREFIX} --enable-drafts
make -j${CPU_COUNT} && make install
sudo ldconfig
```

And then build pyzmq with draft support:

```bash
export ZMQ_PREFIX=${PREFIX}
export ZMQ_DRAFT_API=1
# rpath may be needed to find libzmq at runtime,
# depending on installation
export LDFLAGS="${LDFLAGS:-} -Wl,-rpath,${ZMQ_PREFIX}/lib"
pip install -v pyzmq --no-binary pyzmq
```

By specifying `--no-binary pyzmq`, pip knows to not install the pre-built wheels, and will compile pyzmq from source.

The `ZMQ_PREFIX=$PREFIX` part is only necessary if libzmq is installed somewhere not on the default search path.
If libzmq is installed in {file}`/usr/local` or similar,
only the `ZMQ_DRAFT_API` option is required.

There are examples of the CLIENT-SERVER and RADIO-DISH patterns in the {file}`examples/draft`
directory of the pyzmq repository.
