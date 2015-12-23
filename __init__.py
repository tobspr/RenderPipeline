
# This file includes all classes from the pipeline which are exposed

import os
import sys
import importlib

# Insert the current directory to the path, so we can do relative
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

# Import the classes without a module, otherwise we get problems when trying to
# import the plugins.
for module_src, module_name in [
        ("Code.RenderPipeline", "RenderPipeline"),
        ("Code.Native", "SpotLight"),
        ("Code.Native", "PointLight")
    ]:
    globals()[module_name] = getattr(importlib.import_module(module_src), module_name)
