"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

# This file includes all modules from the native module.
# pylint: disable=invalid-name

from rpcore.rpobject import RPObject

# The native module should only be imported once, and that by the internal pipeline code
# The proper way is: from rpcore import ABC
assert __package__ == "rpcore.native", "Bad pipeline import! Use from rpcore import X"


from .rpnative import (
    GPUCommand,
    GPUCommandList,
    ShadowManager,
    InternalLightManager,
    PSSMCameraRig,
    IESDataset,
    TagStateManager
)

# Import light classes under a different name
from .rpnative import RPSphereLight as SphereLight
from .rpnative import RPSpotLight as SpotLight
from .rpnative import RPRectangleLight as RectangleLight
from .rpnative import RPTubeLight as TubeLight

RPObject.global_debug("RPCORE", "RenderPipeline core modules loaded")
