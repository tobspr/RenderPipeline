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
from __future__ import print_function

# This script just copies the generated .pyd file to the current directory.

import sys
import platform
from shutil import copyfile
from os.path import isfile, join, dirname, realpath, isdir
from panda3d.core import PandaSystem
from common import *


def find_binary():
    """ Returns the path to the generated binary and pdb file """

    # Stores where we find the generated binary
    source_file = None

    # Stores where we find the generated PDB
    pdb_file = None

    possible_files = []
    possible_pdb_files = []

    if is_windows():

        # Check the different Configurations
        configurations = ["RelWithDebInfo", "Release"]
        target_file = MODULE_NAME + ".pyd"

        for config in configurations:
            possible_files.append(join(get_output_dir(), config, MODULE_NAME + ".dll"))

    elif is_linux():
        target_file = MODULE_NAME + ".so"
        possible_files.append(join(get_output_dir(), target_file))

    for file in possible_files:
        if isfile(file):
            source_file = file

            pdb_name = file.replace(".so", ".pdb").replace(".dll", ".pdb")
            if isfile(pdb_name):
                pdb_file = pdb_name

    return source_file, pdb_file, target_file


if __name__ == "__main__":


    if len(sys.argv) != 2:
        fatal_error("Usage: finalize.py <module-name>")

    MODULE_NAME = sys.argv[1]
    source_file, pdb_file, target_file = find_binary()
    target_pdb_file = MODULE_NAME + ".pdb"

    if source_file:
        dest_folder = join(get_script_dir(), "../")

        # Copy the generated DLL
        copyfile(source_file, join(dest_folder, target_file))

        # Copy the generated PDB (if it was generated)
        if pdb_file:
            copyfile(pdb_file, join(dest_folder, target_pdb_file))

    else:
        fatal_error("Failed to find generated binary!")

    sys.exit(0)