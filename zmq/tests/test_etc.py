# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.

import sys

import zmq

from pytest import mark


@mark.skipif('zmq.zmq_version_info() < (4,3)')
def test_has():
    assert not zmq.has('something weird')
    has_ipc = zmq.has('ipc')
    assert has_ipc == sys.platform.startswith('win')


@mark.skipif(not hasattr(zmq, '_libzmq'), reason="bundled libzmq")
def test_has_curve():
    """bundled libzmq has curve support"""
    assert zmq.has('curve')
