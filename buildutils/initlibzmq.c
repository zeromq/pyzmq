#include <Python.h>
/*
This file is from pyzmq-static by Brandon Craig-Rhodes,
and used under the BSD license

Provide the init function that Python expects
when we compile libzmq by pretending it is a Python extension.
*/

static PyMethodDef Methods[] = {
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initlibzmq(void)
{
    (void) Py_InitModule("libzmq", Methods);
}
