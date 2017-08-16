#!/usr/bin/env bash

# example script for installing libzmq and pyzmq with draft support

# 1. install libzmq with draft enabled
export ZMQ_VERSION=4.2.2
export PREFIX=${PREFIX:-/usr/local}
export PYZMQ=${PYZMQ:-pyzmq}

set -ex
echo "installing libzmq to $PREFIX"
wget https://github.com/zeromq/libzmq/releases/download/v${ZMQ_VERSION}/zeromq-${ZMQ_VERSION}.tar.gz -O libzmq.tar.gz
tar -xzf libzmq.tar.gz
cd zeromq-${ZMQ_VERSION}
./configure --prefix=${PREFIX} --enable-drafts
make -j && make install

# install pyzmq with drafts enabled
# --install-option disables installing pyzmq from wheels,
# which do not have draft support

echo "installing ${PYZMQ}"
pip install -v --pre ${PYZMQ} \
  --install-option=--enable-drafts \
  --install-option=--zmq=${PREFIX}

cat << END | python
import sys
import zmq
print('python: %s' % sys.executable)
print(sys.version)
print('pyzmq-%s' % zmq.__version__)
print('libzmq-%s' % zmq.zmq_version())
print('Draft API available: %s' % zmq.DRAFT_API)
END
