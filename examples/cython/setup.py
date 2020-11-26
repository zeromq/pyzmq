from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize

import numpy
import zmq

extensions = [
    Extension(
        "cyzmq_example",
        ["cyzmq.pyx"],
        include_dirs=zmq.get_includes() + [numpy.get_include()],
    )
]
setup(name="cython-zmq-example", ext_modules=cythonize(extensions))
