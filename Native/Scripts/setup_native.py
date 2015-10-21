from __future__ import print_function

import os
import sys
import subprocess
import platform



devnull = open(os.path.devnull, "w")
current_dir = os.getcwd()

def error(*args):
    print(*args, file=sys.stderr)
    sys.exit(1)

output_path = ""

if platform.system() == "Windows":
    output_path = "../Windows/"
elif platform.system() == "Linux":
    output_path = "../Linux/"
else:
    error("Unsupported Platform!")

if not os.path.isdir(output_path):
    try:
        os.makedirs(output_pth)
    except:
        error("Failed to create output dir!")

os.chdir(output_path)

print("Running cmake ..")

cmake_args = []

if platform.system() == "Windows":
    
    # find visual studio studio
    from vc_api import get_installed_vc_versions
    versions = get_installed_vc_versions()
    if "10.0" in versions:
        cmake_args += ['-GVisual Studio 10 2010']
    else:
        if len(versions) < 1:
            print("WARNING: No installed Visual Studio version found! Trying to")
            print("compile with default compiler, but this might fail!")
        else:
            print("WARNING: Could not find Visual studio 2010! Trying to compile with")
            print("default compiler, but this might fail!")
            print("Installed visual studio versions: " + ','.join(versions.keys()))


try:
    subprocess.check_output(["cmake", "../"] + cmake_args, stderr=sys.stderr)
except Exception as msg:
    error("cmake failed:", msg)

print("Compiling solution ..")
os.chdir(current_dir)

try:
    subprocess.check_output(["python", "compile.py"], stderr=sys.stderr)
except Exception as msg:
    error("Compilation failed:", msg)


# Check if the generated binary exists
if platform.system() == "Windows":
    expected_bin = "RSNative.pyd"
elif platform.system() == "Linux":
    expected_bin = "RSNative.so"


if not os.path.isfile("../" + expected_bin):
    error("Compilation finished but could not find binary (" + expected_bin + ")!")


print("Success!")
sys.exit(0)