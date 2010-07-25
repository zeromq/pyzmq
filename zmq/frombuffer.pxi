# copied,adapted from mpi4py
# Jul 23, 2010 18:00 PST (r539)
# http://code.google.com/p/mpi4py/source/browse/trunk/src/MPI/asbuffer.pxi
# Copyright (c) 2009, Lisandro Dalcin.
# All rights reserved.
# BSD License: http://www.opensource.org/licenses/bsd-license.php
# 
#------------------------------------------------------------------------------
# Python 3 buffer interface (PEP 3118)
include "versioner.pxi"
IF NEWSTYLE:
    cdef extern from "Python.h":
        ctypedef struct PyMemoryViewObject:
            pass
        ctypedef struct Py_buffer:
            void *buf
            Py_ssize_t len
            Py_ssize_t itemsize
            char *format
            Py_ssize_t shape
        cdef enum:
            PyBUF_SIMPLE
            PyBUF_WRITABLE
            PyBUF_FORMAT
            PyBUF_ANY_CONTIGUOUS
        void PyBuffer_Release(Py_buffer *)
        int  PyObject_CheckBuffer(object)
        int  PyObject_GetBuffer(object, Py_buffer *, int) except -1
        int PyBuffer_FillInfo(Py_buffer *view, object obj, void *buf, Py_ssize_t len, int readonly, int infoflags) except -1
        cdef object PyMemoryView_FromBuffer(Py_buffer *info)

# Python 2 buffer interface (legacy)
ELSE:
    cdef extern from "Python.h":
        int PyObject_CheckReadBuffer(object)
        cdef object PyBuffer_FromMemory(void *ptr, Py_ssize_t s)
        cdef object PyBuffer_FromReadWriteMemory(void *ptr, Py_ssize_t s)# except -1

#------------------------------------------------------------------------------

IF NEWSTYLE:
    cdef object frombuffer(void *ptr, Py_ssize_t s, int readonly):
        cdef Py_buffer pybuf
        cdef Py_ssize_t *shape = [s]
        cdef str astr=""
        PyBuffer_FillInfo(&pybuf, astr, ptr, s, readonly, PyBUF_SIMPLE)
        pybuf.format = "B"
        pybuf.shape = shape
        return PyMemoryView_FromBuffer(&pybuf)
ELSE:
    cdef object frombuffer(void *ptr, Py_ssize_t s, int readonly):
        if readonly:
            return PyBuffer_FromMemory(ptr, s)
        else:
            return PyBuffer_FromReadWriteMemory(ptr, s)

cdef inline object frombuffer_r(void *ptr, Py_ssize_t s):
    return frombuffer(ptr, s, 1)

cdef inline object frombuffer_w(void *ptr, Py_ssize_t s):
    return frombuffer(ptr, s, 0)

#------------------------------------------------------------------------------
