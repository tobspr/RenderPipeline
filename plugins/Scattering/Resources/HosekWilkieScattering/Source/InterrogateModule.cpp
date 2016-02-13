
#include "dtoolbase.h"
#include "interrogate_request.h"

#include "py_panda.h"

extern LibraryDef HSWKScattering_moddef;
extern void Dtool_HSWKScattering_RegisterTypes();
extern void Dtool_HSWKScattering_ResolveExternals();
extern void Dtool_HSWKScattering_BuildInstants(PyObject *module);

#if PY_MAJOR_VERSION >= 3 || !defined(NDEBUG)
#ifdef _WIN32
extern "C" __declspec(dllexport) PyObject *PyInit_HSWKScattering();
#elif __GNUC__ >= 4
extern "C" __attribute__((visibility("default"))) PyObject *PyInit_HSWKScattering();
#else
extern "C" PyObject *PyInit_HSWKScattering();
#endif
#endif
#if PY_MAJOR_VERSION < 3 || !defined(NDEBUG)
#ifdef _WIN32
extern "C" __declspec(dllexport) void initHSWKScattering();
#elif __GNUC__ >= 4
extern "C" __attribute__((visibility("default"))) void initHSWKScattering();
#else
extern "C" void initHSWKScattering();
#endif
#endif

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef py_HSWKScattering_module = {
  PyModuleDef_HEAD_INIT,
  "HSWKScattering",
  NULL,
  -1,
  NULL,
  NULL, NULL, NULL, NULL
};

PyObject *PyInit_HSWKScattering() {
  PyImport_Import(PyUnicode_FromString("panda3d.core"));
  Dtool_HSWKScattering_RegisterTypes();
  Dtool_HSWKScattering_ResolveExternals();

  LibraryDef *defs[] = {&HSWKScattering_moddef, NULL};

  PyObject *module = Dtool_PyModuleInitHelper(defs, &py_HSWKScattering_module);
  if (module != NULL) {
    Dtool_HSWKScattering_BuildInstants(module);
  }
  return module;
}

#ifndef NDEBUG
void initHSWKScattering() {
  PyErr_SetString(PyExc_ImportError, "HSWKScattering was compiled for Python " PY_VERSION ", which is incompatible with Python 2");
}
#endif
#else  // Python 2 case

void initHSWKScattering() {
  PyImport_Import(PyUnicode_FromString("panda3d.core"));
  Dtool_HSWKScattering_RegisterTypes();
  Dtool_HSWKScattering_ResolveExternals();

  LibraryDef *defs[] = {&HSWKScattering_moddef, NULL};

  PyObject *module = Dtool_PyModuleInitHelper(defs, "HSWKScattering");
  if (module != NULL) {
    Dtool_HSWKScattering_BuildInstants(module);
  }
}

#ifndef NDEBUG
PyObject *PyInit_HSWKScattering() {
  PyErr_SetString(PyExc_ImportError, "HSWKScattering was compiled for Python " PY_VERSION ", which is incompatible with Python 3");
  return (PyObject *)NULL;
}
#endif
#endif

