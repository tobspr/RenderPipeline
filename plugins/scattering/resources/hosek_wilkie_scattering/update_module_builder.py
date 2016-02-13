"""
This script downloads and updates the module builder.
"""

ignore = ("__init__.py LICENSE README.md config.ini "
    "Source/ExampleClass.cpp Source/ExampleClass.h Source/ExampleClass.I").split()
import os
import sys
curr_dir = os.path.dirname(os.path.realpath(__file__));
os.chdir(curr_dir);
sys.path.insert(0, "../" * 4); sys.path.insert(0, "../" * 4 + "Code/External/six")
from code.Util.SubmoduleDownloader import SubmoduleDownloader
SubmoduleDownloader.download_submodule("tobspr", "P3DModuleBuilder", curr_dir, ignore)
with open("scripts/__init__.py", "w") as handle: pass
try: os.remove(".gitignore")
except: pass
os.rename("prefab.gitignore", ".gitignore")
