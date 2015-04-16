#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

import os, sys
import warnings

warnings.warn("setupegg.py is deprecated. Don't use it anymore, it's a bit silly.")

# now, import setuptools and call the actual setup
import setuptools
try:
    execfile('setup.py')
except NameError:
    exec( open('setup.py','rb').read() )
