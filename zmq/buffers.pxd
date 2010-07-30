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
    ctypedef int Py_ssize_t
    ctypedef struct PyMemoryViewObject:
        pass
    ctypedef struct Py_buffer:
        void *buf
        Py_ssize_t len
        Py_ssize_t itemsize
        char *format
        Py_ssize_t *shape
    cdef enum:
        PyBUF_SIMPLE
        PyBUF_WRITABLE
        PyBUF_FORMAT
        PyBUF_ANY_CONTIGUOUS
    int  PyObject_CheckBuffer(object)
    int  PyObject_GetBuffer(object, Py_buffer *, int) except -1
    void PyBuffer_Release(Py_buffer *)
    
    int PyBuffer_FillInfo(Py_buffer *view, object obj, void *buf, Py_ssize_t len, int readonly, int infoflags) except -1
    object PyMemoryView_FromBuffer(Py_buffer *info)
    
    object PyMemoryView_FromObject(object)

# Python 2 buffer interface (legacy)
cdef extern from "Python.h":
    ctypedef void const_void "const void"
    Py_ssize_t Py_END_OF_BUFFER
    int PyObject_CheckReadBuffer(object)
    int PyObject_AsReadBuffer (object, const_void **, Py_ssize_t *) except -1
    int PyObject_AsWriteBuffer(object, void **, Py_ssize_t *) except -1
    
    object PyBuffer_FromMemory(void *ptr, Py_ssize_t s)
    object PyBuffer_FromReadWriteMemory(void *ptr, Py_ssize_t s)

    object PyBuffer_FromObject(object, Py_ssize_t offset, Py_ssize_t size)
    object PyBuffer_FromReadWriteObject(object, Py_ssize_t offset, Py_ssize_t size)


#------------------------------------------------------------------------------
# asbuffer: C buffer from python object

cdef inline int is_buffer(object ob):
    return (PyObject_CheckBuffer(ob) or
            PyObject_CheckReadBuffer(ob))

cdef inline object asbuffer(object ob, int writable, int format,
                     void **base, Py_ssize_t *size, Py_ssize_t *itemsize):

    cdef void *bptr = NULL
    cdef Py_ssize_t blen = 0, bitemlen = 0
    cdef str bfmt = None
    cdef Py_buffer view
    cdef int flags = PyBUF_SIMPLE
    # if not is_buffer(ob):
    #     raise TypeError("%s not a buffer"%(type(ob)))
    if PyObject_CheckBuffer(ob):
        flags = PyBUF_ANY_CONTIGUOUS
        if writable:
            flags |= PyBUF_WRITABLE
        if format:
            flags |= PyBUF_FORMAT
        PyObject_GetBuffer(ob, &view, flags)
        bptr = view.buf
        blen = view.len
        if format:
            if view.format != NULL:
                bfmt = view.format
                bitemlen = view.itemsize
        PyBuffer_Release(&view)
    else:
        if writable:
            PyObject_AsWriteBuffer(ob, &bptr, &blen)
        else:
            PyObject_AsReadBuffer(ob, <const_void **>&bptr, &blen)
        if format:
            try: # numpy.ndarray
                dtype = ob.dtype
                bfmt = dtype.char
                bitemlen = dtype.itemsize
            except AttributeError:
                try: # array.array
                    bfmt = ob.typecode
                    bitemlen = ob.itemsize
                except AttributeError:
                    if isinstance(ob, bytes):
                        bfmt = "B"
                        bitemlen = 1
                    else:
                        # nothing found
                        bfmt = None
                        bitemlen = 0
    if base: base[0] = <void *>bptr
    if size: size[0] = <Py_ssize_t>blen
    if itemsize: itemsize[0] = <Py_ssize_t>bitemlen
    return bfmt

cdef inline object asbuffer_r(object ob, void **base, Py_ssize_t *size):
    asbuffer(ob, 0, 0, base, size, NULL)
    return ob

cdef inline object asbuffer_w(object ob, void **base, Py_ssize_t *size):
    asbuffer(ob, 1, 0, base, size, NULL)
    return ob

#------------------------------------------------------------------------------
# frombuffer: python buffer/view from C buffer

cdef inline object frombuffer_3(void *ptr, Py_ssize_t s, int readonly):
    # Python 3 model, will work on Python >= 2.6
    # we only use it for Python >= 3
    cdef Py_buffer pybuf
    cdef Py_ssize_t *shape = [s]
    cdef str astr=""
    PyBuffer_FillInfo(&pybuf, astr, ptr, s, readonly, PyBUF_SIMPLE)
    pybuf.format = "B"
    pybuf.shape = shape
    return PyMemoryView_FromBuffer(&pybuf)

cdef inline object frombuffer_2(void *ptr, Py_ssize_t s, int readonly):
    # must use this for Python <= 2.6
    # we use it for all Python < 3
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
# viewfromobject: python buffer/view from python object, refcounts intact
# frombuffer(asbuffer(obj)) would lose track of refs

cdef inline object viewfromobject(object obj, int readonly):

    if PY_MAJOR_VERSION < 3:
        if readonly:
            return PyBuffer_FromObject(obj, 0, Py_END_OF_BUFFER)
        else:
            return PyBuffer_FromReadWriteObject(obj, 0, Py_END_OF_BUFFER)
    else:
        return PyMemoryView_FromObject(obj)

cdef inline object viewfromobject_r(object obj):
    return viewfromobject(obj, 1)

cdef inline object viewfromobject_w(object obj):
    return viewfromobject(obj, 0)

