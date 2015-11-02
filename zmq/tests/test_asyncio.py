"""Test asyncio support"""
# Copyright (c) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import zmq

from zmq.tests import BaseZMQTestCase, SkipTest

try:
    import asynciox
except ImportError:
    try:
        import trollius
    except ImportError:
        class TestAsyncIOSocket(BaseZMQTestCase):
            def test_noop(self):
                raise SkipTest("No asyncio library")
    else:
        from ._test_trollius import TestAsyncIOSocket
else:
    from ._test_asyncio import TestAsyncIOSocket
    
