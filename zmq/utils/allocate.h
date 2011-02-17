/*
A utility to allocate a C array.

This is excerpted from mpi4py's "atimport.h" and is licensed under the BSD license.
*/

#include "Python.h"

static PyObject * allocate(Py_ssize_t n, void **pp){
  PyObject *ob;
  if (n > PY_SSIZE_T_MAX)
    return PyErr_NoMemory();
  else if (n < 0) {
    PyErr_SetString(PyExc_RuntimeError,
                    "memory allocation with negative size");
    return NULL;
  }
#if PY_VERSION_HEX >= 0x02060000
  ob = PyByteArray_FromStringAndSize(NULL, (n==0) ? 1 : n);
  if (ob && n==0 && (PyByteArray_Resize(ob, 0) < 0)) {
    Py_DECREF(ob);
    return NULL;
  }
  if (ob && pp)
    *pp = (void *)PyByteArray_AS_STRING(ob);
#else
  {
    void *p = PyMem_Malloc(n);
    if (!p)
      return PyErr_NoMemory();
    ob = PyCObject_FromVoidPtr(p, PyMem_Free);
    if (!ob)
      PyMem_Free(p);
    else if (pp)
      *pp = p;
  }
#endif
  return ob;
}