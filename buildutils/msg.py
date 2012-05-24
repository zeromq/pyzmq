"""logging"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq, copied and adapted from h5py.
#  h5py source used under the New BSD license
#
#  h5py: <http://code.google.com/p/h5py/>
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

from __future__ import division

import sys
import logging

#-----------------------------------------------------------------------------
# Logging (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------


logger = logging.getLogger()
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

