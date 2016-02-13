
#include "dtoolbase.h"
#include "interrogate_request.h"

#include "py_panda.h"

extern LibraryDef RSNative_moddef;
extern void Dtool_RSNative_RegisterTypes();
extern void Dtool_RSNative_ResolveExternals();
extern void Dtool_RSNative_BuildInstants(PyObject *module);

#if PY_MAJOR_VERSION >= 3 || !defined(NDEBUG)
#ifdef _WIN32
extern "C" __declspec(dllexport) PyObject *PyInit_RSNative();
#elif __GNUC__ >= 4
extern "C" __attribute__((visibility("default"))) PyObject *PyInit_RSNative();
#else
extern "C" PyObject *PyInit_RSNative();
#endif
#endif
#if PY_MAJOR_VERSION < 3 || !defined(NDEBUG)
#ifdef _WIN32
extern "C" __declspec(dllexport) void initRSNative();
#elif __GNUC__ >= 4
extern "C" __attribute__((visibility("default"))) void initRSNative();
#else
extern "C" void initRSNative();
#endif
#endif

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef py_RSNative_module = {
  PyModuleDef_HEAD_INIT,
  "RSNative",
  NULL,
  -1,
  NULL,
  NULL, NULL, NULL, NULL
};

PyObject *PyInit_RSNative() {
  PyImport_Import(PyUnicode_FromString("panda3d.core"));
  Dtool_RSNative_RegisterTypes();
  Dtool_RSNative_ResolveExternals();

  LibraryDef *defs[] = {&RSNative_moddef, NULL};

  PyObject *module = Dtool_PyModuleInitHelper(defs, &py_RSNative_module);
  if (module != NULL) {
    Dtool_RSNative_BuildInstants(module);
  }
  return module;
}

#ifndef NDEBUG
void initRSNative() {
  PyErr_SetString(PyExc_ImportError, "RSNative was compiled for Python " PY_VERSION ", which is incompatible with Python 2");
}
#endif
#else  // Python 2 case

void initRSNative() {
  PyImport_Import(PyUnicode_FromString("panda3d.core"));
  Dtool_RSNative_RegisterTypes();
  Dtool_RSNative_ResolveExternals();

  LibraryDef *defs[] = {&RSNative_moddef, NULL};

  PyObject *module = Dtool_PyModuleInitHelper(defs, "RSNative");
  if (module != NULL) {
    Dtool_RSNative_BuildInstants(module);
  }
}

#ifndef NDEBUG
PyObject *PyInit_RSNative() {
  PyErr_SetString(PyExc_ImportError, "RSNative was compiled for Python " PY_VERSION ", which is incompatible with Python 3");
  return (PyObject *)NULL;
}
#endif
#endif

