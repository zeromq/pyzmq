#!/usr/bin/env bash

# example script for installing libzmq and pyzmq with draft support

# 1. install libzmq with draft enabled
ZMQ_VERSION=4.3.4
PREFIX=${PREFIX:-/usr/local}
PYZMQ=${PYZMQ:-pyzmq}
CPU_COUNT=${CPU_COUNT:-$(python3 -c "import os; print(os.cpu_count())")}

set -ex
echo "installing libzmq to $PREFIX"
wget https://github.com/zeromq/libzmq/releases/download/v${ZMQ_VERSION}/zeromq-${ZMQ_VERSION}.tar.gz -O libzmq.tar.gz
tar -xzf libzmq.tar.gz
cd zeromq-${ZMQ_VERSION}
./configure --prefix=${PREFIX} --enable-drafts
make -j${CPU_COUNT} && make install

# install pyzmq with drafts enabled
# By specifying ``--no-binary pyzmq``, pip knows to not install wheels, and will compile pyzmq from source.

echo "installing ${PYZMQ}"
export ZMQ_PREFIX=${PREFIX}
export ZMQ_DRAFT_API=1

pip install -v --no-binary pyzmq --pre ${PYZMQ}

cat << END | python3
import sys
import zmq
print('python: %s' % sys.executable)
print(sys.version)
print('pyzmq-%s' % zmq.__version__)
print('libzmq-%s' % zmq.zmq_version())
print('Draft API available: %s' % zmq.DRAFT_API)
END
