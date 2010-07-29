# copied,adapted from mpi4py
# Jul 23, 2010 18:00 PST (r539)
# http://code.google.com/p/mpi4py/source/browse/trunk/src/MPI/asbuffer.pxi
# Copyright (c) 2009, Lisandro Dalcin.
# All rights reserved.
# BSD License: http://www.opensource.org/licenses/bsd-license.php
# 
#------------------------------------------------------------------------------
# Python 3 buffer interface (PEP 3118)
cdef extern from "Python.h":
    int PY_MAJOR_VERSION
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
    object PyMemoryView_FromBuffer(Py_buffer *info)

# Python 2 buffer interface (legacy)
cdef extern from "Python.h":
    int PyObject_CheckReadBuffer(object)
    object PyBuffer_FromMemory(void *ptr, Py_ssize_t s)
    object PyBuffer_FromReadWriteMemory(void *ptr, Py_ssize_t s)

#------------------------------------------------------------------------------

cdef object frombuffer_3(void *ptr, Py_ssize_t s, int readonly):
    # Python 3 model, will work on Python >= 2.6
    cdef Py_buffer pybuf
    cdef Py_ssize_t *shape = [s]
    cdef str astr=""
    PyBuffer_FillInfo(&pybuf, astr, ptr, s, readonly, PyBUF_SIMPLE)
    pybuf.format = "B"
    pybuf.shape = shape
    return PyMemoryView_FromBuffer(&pybuf)

cdef object frombuffer_2(void *ptr, Py_ssize_t s, int readonly):
    # must use this for Python <= 2.6
    if readonly:
        return PyBuffer_FromMemory(ptr, s)
    else:
        return PyBuffer_FromReadWriteMemory(ptr, s)

cdef inline object frombuffer(void *ptr, Py_ssize_t s, int readonly):

    if PY_MAJOR_VERSION < 3:
        return frombuffer_2(ptr, s, readonly)
    else:
        return frombuffer_3(ptr, s, readonly)

cdef inline object frombuffer_r(void *ptr, Py_ssize_t s):
    return frombuffer(ptr, s, 1)

cdef inline object frombuffer_w(void *ptr, Py_ssize_t s):
    return frombuffer(ptr, s, 0)

#------------------------------------------------------------------------------
