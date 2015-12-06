
# This file includes all modules from the RSNative module.
from __future__ import print_function
from direct.stdpy.file import join, isfile
from os.path import dirname, realpath
pyd_path = dirname(realpath(__file__))

# If the module was built, use it, otherwise use the python wrappers
if isfile(join(pyd_path, "RSNative.pyd")) or isfile(join(pyd_path, "RSNative.so")):
    print("[>] CORE  Using native core module")
    from .RSNative import GPUCommand, GPUCommandList, LightStorage, PSSMCameraRig, IESDataset
    from .RSNative import RPPointLight as PointLight
    from .RSNative import RPSpotLight as SpotLight
else:

    print("[>] CORE  Using simulated python core module")
    from .PythonImpl import GPUCommand, GPUCommandList, LightStorage, PSSMCameraRig, IESDataset
    from .PythonImpl import RPPointLight as PointLight
    from .PythonImpl import RPSpotLight as SpotLight
