# coding: utf-8
"""0MQ Frame pure Python methods."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from .attrsettr import AttributeSetter
from zmq.backend import Frame as FrameBase
import zmq

def _draft(v, feature):
    zmq.error._check_version(v, feature)
    if not zmq.DRAFT_API:
        raise RuntimeError("libzmq and pyzmq must be built with draft support for %s" % features)

class Frame(FrameBase, AttributeSetter):
    def __getitem__(self, key):
        # map Frame['User-Id'] to Frame.get('User-Id')
        return self.get(key)

    @property
    def group(self):
        _draft((4,2), "RADIO-DISH")
        return self.get('group')

    @group.setter
    def group(self, group):
        _draft((4,2), "RADIO-DISH")
        self.set('group', group)

    @property
    def routing_id(self):
        _draft((4,2), "CLIENT-SERVER")
        return self.get('routing_id')

    @routing_id.setter
    def routing_id(self, routing_id):
        _draft((4,2), "CLIENT-SERVER")
        self.set('routing_id', routing_id)


# keep deprecated alias
Message = Frame
__all__ = ['Frame', 'Message']
