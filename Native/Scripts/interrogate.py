from __future__ import print_function

import sys
import platform
from os import system, getcwd, listdir
from direct.stdpy.file import join, isfile, isdir
import subprocess


if len(sys.argv) != 4:
    print("Invalid arguments!", file=sys.stderr)
    print("Arguments must be: [panda-bin] [panda-libs] [panda-include]", file=sys.stderr)
    sys.exit(1)

# Parameters
PANDA_BIN = sys.argv[1]
PANDA_LIBS = sys.argv[2]
PANDA_INCLUDE = sys.argv[3]
MODULE_NAME = "RSNative"


COMPILER="MSVC" if platform.system() == "Windows" else "GCC"
IS_64_BIT=sys.maxsize > 2 ** 32

cwd = getcwd().replace("\\", "/").rstrip("/")

ignoreFiles = ["InterrogateModule.cpp", "InterrogateWrapper.cpp"]

def check_ignore(source):
    for f in ignoreFiles:
        if f.lower() in source.lower():
            return False
    return True


def find_sources(base_dir):
    sources = []
    files = listdir(base_dir)
    for f in files:
        fpath = join(base_dir, f)
        if isfile(fpath) and check_ignore(f) and f.endswith(".h"):
            sources.append(fpath)
        elif isdir(fpath):
            sources += find_sources(fpath)

    return sources


all_sources = find_sources("Source/")

# Strip path
all_sources = [i.replace("Source/", "") for i in all_sources]

# print("\nRunning interrogate ..")

cmd = [PANDA_BIN + '/interrogate']
cmd += ["-fnames", "-string", "-refcount", "-assert", "-python-native"]
cmd += ["-S" + PANDA_INCLUDE + "/parser-inc"]
cmd += ["-S" + PANDA_INCLUDE + "/"]

# Add all subdirectories
for pth in listdir("Source/"):
    if isdir(join("Source/", pth)):
        cmd += ["-I" + join("Source/", pth)]

cmd += ["-srcdir",  join(cwd, "Source") ]

cmd += ["-oc", "Source/InterrogateWrapper.cpp"]
cmd += ["-od", "Source/Interrogate.in"]
cmd += ["-module", MODULE_NAME]
cmd += ["-library", MODULE_NAME]

cmd += ["-nomangle"]

# Defines required to parse the panda source
defines = ["INTERROGATE", "CPPPARSER", "__STDC__=1", "__cplusplus=201103L"]

if COMPILER=="MSVC":
    defines += ["__inline", "_X86_", "WIN32_VC", "WIN32", "_WIN32"]
    if IS_64_BIT:
        defines += ["WIN64_VC", "WIN64", "_WIN64"]
    # NOTE: this 1600 value is the version number for VC2010.
    defines += ["_MSC_VER=1600", '"__declspec(param)="', "__cdecl", "_near", "_far", "__near", "__far", "__stdcall"]

if COMPILER=="GCC":
    defines += ['__attribute__\(x\)=']
    if IS_64_BIT:
        defines += ['_LP64']
    else:
        defines += ['__i386__']

for define in defines:
    cmd += ["-D" + define]
cmd += all_sources

try:
    subprocess.check_output(cmd, stderr=sys.stderr)
except subprocess.CalledProcessError as msg:
    print("Error executing interrogate command:", msg, msg.output, file=sys.stderr)
    sys.exit(1)


# print("\nRunning interrogate_module ..")
cmd = [PANDA_BIN + "/interrogate_module"]
cmd += ["-python-native"]
cmd += ["-import", "panda3d.core"] 
cmd += ["-module", MODULE_NAME] 
cmd += ["-library", MODULE_NAME] 
cmd += ["-oc", "Source/InterrogateModule.cpp"] 
cmd += ["Source/Interrogate.in"]

try:
    subprocess.check_output(cmd, stderr=sys.stderr)
except subprocess.CalledProcessError as msg:
    print("Error executing interrogate_module command: ", msg.output, file=sys.stderr)
    sys.exit(1)


sys.exit(0)