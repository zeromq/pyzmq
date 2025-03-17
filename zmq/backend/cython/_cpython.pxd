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
  # cpython.buffer
  cdef enum:
    PyBUF_ANY_CONTIGUOUS,
    PyBUF_WRITABLE
  int PyObject_GetBuffer(object obj, Py_buffer *view, int flags) except -1
  void PyBuffer_Release(Py_buffer *view)
