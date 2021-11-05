import numpy
from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

import zmq

extensions = [
    Extension(
        "cyzmq_example",
        ["cyzmq.pyx"],
        include_dirs=zmq.get_includes() + [numpy.get_include()],
    )
]
setup(name="cython-zmq-example", ext_modules=cythonize(extensions))
