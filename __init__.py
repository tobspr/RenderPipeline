
# This file includes all classes from the pipeline which are exposed


import os
import sys
import importlib

__all__ = ["RenderPipeline", "SpotLight", "PointLight"]

# Insert the current directory to the path, so we can do relative imports
root_pth = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, root_pth)

# Add the six library to the Path for Python 2 and 3 compatiblity. This is handy
# so we can just do "import six" everywhere.
sys.path.insert(0, os.path.join(root_pth, "Code/External/six/"))

# Import the classes without a module, otherwise we get problems when trying to
# import the plugins.
for module_src, module_name in [
        ("Code.RenderPipeline", "RenderPipeline"),
        ("Code.Native", "SpotLight"),
        ("Code.Native", "PointLight")
    ]:
    globals()[module_name] = getattr(importlib.import_module(module_src), module_name)
