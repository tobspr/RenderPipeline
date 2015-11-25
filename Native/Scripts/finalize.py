from __future__ import print_function

# This script just copies the generated .pyd file to the current directory.

import sys
sys.dont_write_bytecode = True


import platform
from shutil import copyfile
from os.path import isfile, join, dirname, realpath, isdir

from panda3d.core import PandaSystem

# Storage for the precompiled render pipeline binaries
BINARY_STORAGE = "E:\Dropbox\Sonstiges\PrecompiledBuilds"

if __name__ == "__main__":

    source_file = None
    curr_dir = dirname(realpath(__file__))

    if platform.system() == "Windows":
        possible_files = [
            "Windows/Release/RSNative.pyd",
            "Windows/x64/Release/RSNative.pyd",
        ]
        target_file = "RSNative.pyd"

    elif platform.system() == "Linux":
        possible_files = [
            "Linux/RSNative.so"
        ]
        target_file = "RSNative.so"

    for file in possible_files:
        file = join(curr_dir, "../", file)
        if isfile(file):
            source_file = file

    if source_file:

        dest_folder = join(curr_dir, "../../Code/Native")

        # Copy the generated DLL
        copyfile(source_file, join(dest_folder, target_file))


        if isdir(BINARY_STORAGE):

            # Copy DLL to the precompiled binary dir
            target_filename = "RSNative_" + PandaSystem.getPlatform() + ".pyd"
            target_filename = join(BINARY_STORAGE, target_filename)

            copyfile(source_file, target_filename)



        # Copy the __init__ template
        copyfile(join(curr_dir, "../Source/init.py.template"), join(dest_folder, "__init__.py"))

    else:
        print("Failed to find source file at", ' or '.join(possible_files), "!")
