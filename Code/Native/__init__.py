
# This file includes all modules from the RSNative module.
from __future__ import print_function
from direct.stdpy.file import join, isfile
from os.path import dirname, realpath
from ..Util.DebugObject import DebugObject

use_cxx = False
pyd_path = dirname(realpath(__file__))
flag_path = join(pyd_path, "use_cxx.flag")
if not isfile(flag_path):
    DebugObject.global_error("CORE", "Could not find cxx flag, please run the setup.py!")
else:
    with open(join(pyd_path, "use_cxx.flag"), "r") as handle:
        use_cxx = handle.read().strip() == "1"

# If the module was built, use it, otherwise use the python wrappers
if use_cxx:
    DebugObject.global_debug("CORE", "Using native core module")
    from .RSNative import GPUCommand, GPUCommandList, LightStorage, PSSMCameraRig, IESDataset
    from .RSNative import RPPointLight as PointLight
    from .RSNative import RPSpotLight as SpotLight
else:
    DebugObject.global_debug("CORE", "Using simulated python-wrapper module")
    from .PythonImpl import GPUCommand, GPUCommandList, LightStorage, PSSMCameraRig, IESDataset
    from .PythonImpl import RPPointLight as PointLight
    from .PythonImpl import RPSpotLight as SpotLight
