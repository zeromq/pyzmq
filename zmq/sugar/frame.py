# coding: utf-8
"""0MQ Frame pure Python methods."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from .attrsettr import AttributeSetter
from zmq.backend import Frame as FrameBase
import zmq
from zmq.error import _check_version


class Frame(FrameBase, AttributeSetter):
    def __getitem__(self, key):
        # map Frame['User-Id'] to Frame.get('User-Id')
        return self.get(key)

    @property
    def group(self):
        _check_version((4,2), "RADIO-DISH")
        if not zmq.DRAFT_API:
            raise RuntimeError("libzmq and pyzmq must be built with draft support")
        return self.get('group')

    @group.setter
    def group(self, group):
        _check_version((4,2), "RADIO-DISH")
        if not zmq.DRAFT_API:
            raise RuntimeError("libzmq and pyzmq must be built with draft support")
        self.set('group', group)

    @property
    def routing_id(self):
        print('getting routing id')
        _check_version((4,2), "CLIENT-SERVER")
        if not zmq.DRAFT_API:
            raise RuntimeError("libzmq and pyzmq must be built with draft support")
        return self.get('routing_id')

    @routing_id.setter
    def routing_id(self, routing_id):
        _check_version((4,2), "CLIENT-SERVER")
        if not zmq.DRAFT_API:
            raise RuntimeError("libzmq and pyzmq must be built with draft support")
        self.set('routing_id', routing_id)


# keep deprecated alias
Message = Frame
__all__ = ['Frame', 'Message']
