# coding: utf-8
"""0MQ Frame pure Python methods."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


from .attrsettr import AttributeSetter
from zmq.backend import Frame as FrameBase


class Frame(FrameBase, AttributeSetter):
    def __getitem__(self, key):
        # map Frame['User-Id'] to Frame.get('User-Id')
        return self.get(key)

# keep deprecated alias
Message = Frame
__all__ = ['Frame', 'Message']