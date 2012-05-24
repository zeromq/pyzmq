/*
This file is from pyzmq-static by Brandon Craig-Rhodes,
and used under the BSD license

py3compat from http://wiki.python.org/moin/PortingExtensionModulesToPy3k

Provide the init function that Python expects
when we compile libzmq by pretending it is a Python extension.
*/
#include "Python.h"

static PyMethodDef Methods[] = {
    {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "libzmq",
        NULL,
        -1,
        Methods,
        NULL,
        NULL,
        NULL,
        NULL
};

PyMODINIT_FUNC
PyInit_libzmq(void)
{
    PyObject *module = PyModule_Create(&moduledef);
    return module;
}

#else // py2

PyMODINIT_FUNC
initlibzmq(void)
{
    (void) Py_InitModule("libzmq", Methods);
}

#endif
