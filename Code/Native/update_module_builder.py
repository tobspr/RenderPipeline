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

# This script downloads and updates the module builder.

ignore = ("__init__.py LICENSE README.md config.ini "
    "Source/ExampleClass.cpp Source/ExampleClass.h Source/ExampleClass.I config_module").split()
import os
import sys
curr_dir = os.path.dirname(os.path.realpath(__file__)); os.chdir(curr_dir);
sys.path.insert(0, "../../");sys.path.insert(0, "../../Code/External/six/");
from Code.Util.SubmoduleDownloader import SubmoduleDownloader
SubmoduleDownloader.download_submodule("tobspr", "P3DModuleBuilder", curr_dir, ignore)
with open("Scripts/__init__.py", "w") as handle: pass
try: os.remove(".gitignore")
except: pass
os.rename("prefab.gitignore", ".gitignore")
