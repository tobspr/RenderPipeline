
#include "dtoolbase.h"
#include "interrogate_request.h"

#undef _POSIX_C_SOURCE
#include "py_panda.h"

IMPORT_THIS LibraryDef RPCore_moddef;

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef py_RPCore_module = {
  PyModuleDef_HEAD_INIT,
  "RPCore",
  NULL,
  -1,
  NULL,
  NULL, NULL, NULL, NULL
};

#ifdef _WIN32
extern "C" __declspec(dllexport) PyObject *PyInit_RPCore();
#else
extern "C" PyObject *PyInit_RPCore();
#endif

PyObject *PyInit_RPCore() {
  LibraryDef *defs[] = {&RPCore_moddef, NULL};

  return Dtool_PyModuleInitHelper(defs, &py_RPCore_module);
}

#else  // Python 2 case

#ifdef _WIN32
extern "C" __declspec(dllexport) void initRPCore();
#else
extern "C" void initRPCore();
#endif

void initRPCore() {
  LibraryDef *defs[] = {&RPCore_moddef, NULL};

  Dtool_PyModuleInitHelper(defs, "RPCore");
}
#endif

