"""

This file includes all modules from the native module.

"""

from __future__ import print_function
import sys
import importlib

from direct.stdpy.file import join, isfile
from os.path import dirname, realpath
from ..Util.DebugObject import DebugObject

# Store a global flag, indicating whether the C++ modules were loaded or the python
# implemetation of them
NATIVE_CXX_LOADED = False

# Read the configuration from the flag-file
curr_path = dirname(realpath(__file__))
flag_path = join(curr_path, "use_cxx.flag")
if not isfile(flag_path):
    DebugObject.global_error("CORE", "Could not find cxx flag, please run the setup.py!")
    sys.exit(1)
else:
    with open(join(curr_path, "use_cxx.flag"), "r") as handle:
        NATIVE_CXX_LOADED = handle.read().strip() == "1"

# The native module should only be imported once, and that by the internal pipeline code
# assert __package__ == "Code.Native", "You have included the pipeline in the wrong way!"

# Classes which should get imported
classes_to_import = [
    "GPUCommand",
    "GPUCommandList",
    "LightStorage",
    "PSSMCameraRig",
    "IESDataset",
    "TagStateManager",
]

# Classes which should get imported and renamed
classes_to_import_and_rename = {
    "RPPointLight": "PointLight",
    "RPSpotLight": "SpotLight"
}

native_module = None

# If the module was built, use it, otherwise use the python wrappers
if NATIVE_CXX_LOADED:
    DebugObject.global_debug("CORE", "Using native core module")
    _native_module = importlib.import_module(".RSNative", __package__)
else:
    DebugObject.global_debug("CORE", "Using simulated python-wrapper module")
    _native_module = importlib.import_module(".PythonImpl", __package__)

# Import all classes
for v in classes_to_import + list(classes_to_import_and_rename.keys()):
    if hasattr(_native_module, v):
        v_name = classes_to_import_and_rename[v] if v in classes_to_import_and_rename else v 
        globals()[v_name] = getattr(_native_module, v)
    else:
        print("Warning: could not find property", v)

# Don't export all variables, only the required ones
__all__ = classes_to_import + list(classes_to_import_and_rename.values()) + ["NATIVE_CXX_LOADED"]
