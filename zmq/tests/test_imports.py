# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

# flake8: noqa: F401

from unittest import TestCase

import pytest


class TestImports(TestCase):
    """Test Imports - the quickest test to ensure that we haven't
    introduced version-incompatible syntax errors."""

    def test_toplevel(self):
        """test toplevel import"""
        import zmq

    def test_core(self):
        """test core imports"""
        from zmq import (
            Context,
            Frame,
            Poller,
            Socket,
            constants,
            device,
            proxy,
            pyzmq_version,
            pyzmq_version_info,
            zmq_version,
            zmq_version_info,
        )

    def test_devices(self):
        """test device imports"""
        import zmq.devices
        from zmq.devices import basedevice, monitoredqueue, monitoredqueuedevice

    def test_log(self):
        """test log imports"""
        import zmq.log
        from zmq.log import handlers

    def test_eventloop(self):
        """test eventloop imports"""
        try:
            import tornado
        except ImportError:
            pytest.skip('requires tornado')
        import zmq.eventloop
        from zmq.eventloop import ioloop, zmqstream

    def test_utils(self):
        """test util imports"""
        import zmq.utils
        from zmq.utils import jsonapi, strtypes

    def test_ssh(self):
        """test ssh imports"""
        from zmq.ssh import tunnel

    def test_decorators(self):
        """test decorators imports"""
        from zmq.decorators import context, socket
