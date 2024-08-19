#!/usr/bin/env bash

# example script for installing libzmq and pyzmq with draft support

# tell pyzmq to build bundled libzmq with cmake
# (alternately, install and build libzmq with drafts enabled)
export ZMQ_PREFIX=bundled

# tell pyzmq to build libzmq with draft support
export ZMQ_DRAFT_API=1

# install pyzmq
# By specifying ``--no-binary pyzmq``, pip knows to not install wheels, and will compile pyzmq from source.
# --no-cache prevents installing a previously cached local build of pyzmq

echo "installing pyzmq"
pip install -v --no-cache --no-binary pyzmq pyzmq

cat << END | python3
import sys
import zmq
print('python: %s' % sys.executable)
print(sys.version)
print('pyzmq-%s' % zmq.__version__)
print('libzmq-%s' % zmq.zmq_version())
print('Draft API available: %s' % zmq.DRAFT_API)
END
