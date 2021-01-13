#!/usr/bin/env python3

import pprint

from setuptools import msvc
from setuptools._distutils.util import get_platform

plat = get_platform()
print(f"platform: {plat}")

vcvars = msvc.msvc14_get_vc_env(plat)
print("vcvars:")
pprint.pprint(vcvars)
