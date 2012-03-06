"""Utility to initialize threads."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger, Min Ragan-Kelley
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

cdef extern from "Python.h":
    cdef void PyEval_InitThreads()

# It seems that in only *some* version of Python/Cython we need to call this
# by hand to get threads initialized. Not clear why this is the case though.
# If we don't have this, pyzmq will segfault.
def init_threads():
    PyEval_InitThreads()

__all__ = ['init_threads']
