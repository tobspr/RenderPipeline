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
    except:
        error("Failed to create output dir!")

os.chdir(output_path)

print("Running cmake ..")

cmake_args = []

if platform.system() == "Windows":
   cmake_args += ['-GVisual Studio 10 2010 Win64']

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