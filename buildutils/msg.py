"""logging"""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.

from __future__ import division

import os
import sys
import logging

#-----------------------------------------------------------------------------
# Logging (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------


logger = logging.getLogger()
if os.environ.get('DEBUG'):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stderr))

def debug(msg):
    logger.debug(msg)

def info(msg):
    logger.info(msg)

def fatal(msg, code=1):
    logger.error("Fatal: " + msg)
    exit(code)

def warn(msg):
    logger.error("Warning: " + msg)

def line(c='*', width=48):
    print(c * (width // len(c)))

