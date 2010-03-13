#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

import os, sys

# now, import setuptools and call the actual setup
import setuptools
execfile('setup.py')
