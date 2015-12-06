"""

This script downloads and updates the module builder.

"""


# Dont checkout all files
IGNORE_FILES = [
    "__init__.py",
    ".gitignore",
    "LICENSE",
    "README.md",
    "config.ini",
    "Source/config_module.cpp",
    "Source/config_module.h",
    "Source/ExampleClass.cpp",
    "Source/ExampleClass.h",
    "Source/ExampleClass.I",
]

import sys
import os
sys.path.insert(0, "../../")
from Code.Util.SubmoduleDownloader import SubmoduleDownloader

if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    SubmoduleDownloader.download_submodule("tobspr", "P3DModuleBuilder", curr_dir, IGNORE_FILES)
