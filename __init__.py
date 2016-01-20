"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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

# This file includes all classes from the pipeline which are exposed


# Disable warning about the __all__ variable, since the modules are loaded
# dynamically, and pylint cannot detect that
# pylint: disable=E0603

from __future__ import print_function
import os
import sys
import importlib

# Insert the current directory to the path, so we can do relative imports
RP_ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, RP_ROOT_PATH)

# Add the six library to the Path for Python 2 and 3 compatiblity. This is handy
# so we can just do "import six" everywhere.
sys.path.insert(0, os.path.join(RP_ROOT_PATH, "Code/External/six/"))

# Import the classes without a module, otherwise we get problems when trying to
# import the plugins.
for module_src, module_name in [
        ("Code.RenderPipeline", "RenderPipeline"),
        ("Code.Native", "SpotLight"),
        ("Code.Native", "PointLight")]:
    globals()[module_name] = getattr(importlib.import_module(module_src), module_name)

__all__ = ["RenderPipeline", "SpotLight", "PointLight"]
