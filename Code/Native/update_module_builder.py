"""
This script downloads and updates the module builder.
"""

ignore = ("__init__.py .gitignore LICENSE README.md config.ini Source/config_module.cpp "
    "Source/config_module.h Source/ExampleClass.cpp Source/ExampleClass.h Source/ExampleClass.I").split()

import os
import sys
curr_dir = os.path.dirname(os.path.realpath(__file__)); os.chdir(curr_dir); sys.path.insert(0, "../../")
from Code.Util.SubmoduleDownloader import SubmoduleDownloader
SubmoduleDownloader.download_submodule("tobspr", "P3DModuleBuilder", curr_dir, ignore)
with open("Scripts/__init__.py", "w") as handle: pass
