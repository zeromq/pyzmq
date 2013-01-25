# coding: utf-8
"""0MQ Frame pure Python methods."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .attrsettr import AttributeSetter
from .backend import Frame as FrameBase

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class Frame(FrameBase, AttributeSetter):
    pass

# keep deprecated alias
Message = Frame
__all__ = ['Frame', 'Message']