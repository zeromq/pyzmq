from libc.stdlib cimport free, malloc

# From mpi4py
#---------------------------------------------------------------------

cdef extern from "Python.h":
    object PyCObject_FromVoidPtr(void *, void (*)(void*))

#---------------------------------------------------------------------

cdef inline void *memnew(size_t n):
    if n == 0: n = 1
    return malloc(n)

cdef inline void memdel(void *p):
    if p != NULL: free(p)

cdef inline object allocate(size_t n, void **pp):
    cdef object cob
    cdef void *p = memnew(n)
    if p == NULL: raise MemoryError
    try:    cob = PyCObject_FromVoidPtr(p, memdel)
    except: memdel(p); raise
    pp[0] = p
    return cob