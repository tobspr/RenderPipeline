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
        os.makedirs(output_path)
    except Exception as msg: 
        error("Failed to create output dir:", msg)

os.chdir(output_path)

print("Running cmake ..")

cmake_args = ['-DCMAKE_BUILD_TYPE=Release']

if platform.system() == "Windows":
    
    # find visual studio studio
    from vc_api import get_installed_vc_versions
    versions = get_installed_vc_versions()

    # cmake_args += ['--config', 'Release']

    # Specify 64-bit compiler when using a 64 bit panda sdk build
    bit_suffix = ""
    if platform.architecture()[0] == "64bit":
        bit_suffix = " Win64"

    if "10.0" in versions:
        cmake_args += ['-GVisual Studio 10 2010' + bit_suffix]
    else:
        if len(versions.keys()) < 1:
            print("WARNING: No installed Visual Studio version found! Trying to", file=sys.stderr)
            print("compile with default compiler, but this might fail!", file=sys.stderr)
        else:
            vc_version = list(sorted(versions.keys()))[-1]
            
            print("WARNING: Could not find Visual studio 2010! Trying to compile with", file=sys.stderr)
            print("highest visual studio version (" + vc_version + "), but this might fail!", file=sys.stderr)
            print("Installed visual studio versions: " + ','.join(versions.keys()), file=sys.stderr)

            vc_int_version = int(float(vc_version))

            cmake_args += ['-GVisual Studio ' + str(vc_int_version) + bit_suffix]
        



try:
    subprocess.check_output(["cmake", "../"] + cmake_args, stderr=sys.stderr)
except subprocess.CalledProcessError as msg:
    error("Cmake Error:", msg.output)

print("Compiling solution ..")
os.chdir(current_dir)

try:
    subprocess.check_output(["python", "-B", "compile.py"], stderr=sys.stderr)
except subprocess.CalledProcessError as msg:
    error("Compilation failed:", msg.output)

# Check if the generated binary exists
if platform.system() == "Windows":
    expected_bin = "RSNative.pyd"
elif platform.system() == "Linux":
    expected_bin = "RSNative.so"


if not os.path.isfile("../../Code/Native/" + expected_bin):
    error("Compilation finished but could not find binary (" + expected_bin + ")!")


print("Success!")
sys.exit(0)