#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

import os, sys

# now, import setuptools and call the actual setup
import setuptools
try:
    execfile('setup.py')
except NameError:
    exec( open('setup.py','rb').read() )
