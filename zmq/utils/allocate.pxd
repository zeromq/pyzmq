"""A utility to allocate a C array.

This was copied from mpi4py and is licensed under the BSD license.
"""

from libc.stdlib cimport free, malloc

#-----------------------------------------------------------------------------
# Python includes.
#-----------------------------------------------------------------------------

cdef extern from "Python.h":
    object PyCObject_FromVoidPtr(void *, void (*)(void*))

#-----------------------------------------------------------------------------
# Main functions.
#-----------------------------------------------------------------------------

cdef inline void *memnew(size_t n):
    """malloc a new memory chunk of a given size."""
    if n == 0: n = 1
    return malloc(n)

cdef inline void memdel(void *p):
    """free a chunk of memory allocated with memnew."""
    if p != NULL: free(p)

cdef inline object allocate(size_t n, void **pp):
    """A wrapper that allocates a C array, but with Python ref-counting."""
    cdef object cob
    cdef void *p = memnew(n)
    if p == NULL:
        raise MemoryError()
    try:
        cob = PyCObject_FromVoidPtr(p, memdel)
    except:
        memdel(p)
        raise
    pp[0] = p
    return cob
