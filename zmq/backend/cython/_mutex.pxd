cdef extern from "mutex.h" nogil:
    ctypedef struct mutex_t:
        pass
    cdef mutex_t* mutex_allocate()
    cdef void mutex_dallocate(mutex_t*)
    cdef int mutex_lock(mutex_t*)
    cdef int mutex_unlock(mutex_t*)
