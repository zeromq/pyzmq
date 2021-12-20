"""logging"""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.


import logging
import os
import sys

# -----------------------------------------------------------------------------
# Logging (adapted from h5py: https://www.h5py.org/)
# -----------------------------------------------------------------------------


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
