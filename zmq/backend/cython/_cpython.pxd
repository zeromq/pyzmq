# These should be cimported from cpython.bytes
# but that has a transitive import of cpython.type
# which currently conflicts with limited API
cdef extern from "Python.h":
  # cpython.bytes
  char* PyBytes_AsString(object string) except NULL
  bytes PyBytes_FromStringAndSize(char *v, Py_ssize_t len)
  Py_ssize_t PyBytes_Size(object string) except -1
  # cpython.exc
  int PyErr_CheckSignals() except -1
