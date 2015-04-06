/*
This file is from pyzmq-static by Brandon Craig-Rhodes,
and used under the BSD license

py3compat from http://wiki.python.org/moin/PortingExtensionModulesToPy3k

Provide the init function that Python expects
when we compile libsodium by pretending it is a Python extension.
*/
#include "Python.h"

static PyMethodDef Methods[] = {
    {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "libsodium",
        NULL,
        -1,
        Methods,
        NULL,
        NULL,
        NULL,
        NULL
};

PyMODINIT_FUNC
PyInit_libsodium(void)
{
    PyObject *module = PyModule_Create(&moduledef);
    return module;
}

#else // py2

PyMODINIT_FUNC
initlibsodium(void)
{
    (void) Py_InitModule("libsodium", Methods);
}

#endif
