from __future__ import print_function

import platform
import subprocess
import sys
sys.dont_write_bytecode = True

from os import system
from os.path import isfile, dirname, realpath, join


NATIVE_SRC = join(dirname(realpath(__file__)), "..")
SOLUTION_PATH = join(NATIVE_SRC, "Windows/RSNative.sln")

def hint_manually_msvc():
    print("Could not automatically compile the project! Please head over to", file=sys.stderr)
    print("Native/Windows/ and compile the solution RSNative.sln in release mode!", file=sys.stderr)
    sys.exit(1)

def do_compile():
    print("Trying to compile the solution ..")

    if platform.system() != "Windows":
        print("ERROR: Only windows supported yet, to build on linux", file=sys.stderr)
        print("cd into Linux/ and manually compile with g++", file=sys.stderr)
        sys.exit(1)

    devenv_pth = "C:/Program Files (x86)/Microsoft Visual Studio 10.0/Common7/IDE/devenv.exe"
    if not isfile(devenv_pth):
        print("devenv.exe not found! Expected it at:", devenv_pth, file=sys.stderr)
        return hint_manually_msvc()

    try:
        output = subprocess.check_output([devenv_pth, SOLUTION_PATH, "/build", "Release", "/projectconfig", "Release"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as msg:
        print("Compilation-Error:", msg, file=sys.stderr)
        return hint_manually_msvc()

    print("Success!")
    sys.exit(0)

do_compile()
