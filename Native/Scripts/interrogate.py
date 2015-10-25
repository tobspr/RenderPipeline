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

VERBOSE = False

PANDA_BIN = sys.argv[1]
PANDA_LIBS = sys.argv[2]
PANDA_INCLUDE = sys.argv[3]
MODULE_NAME = "RSNative"


COMPILER = "MSVC" if platform.system() == "Windows" else "GCC"
IS_64_BIT = sys.maxsize > 2 ** 32
USE_ABS_PATH = platform.system() == "Windows"


# Extract cwd and convert it to a valid filepath
cwd = getcwd().replace("\\", "/").rstrip("/")

# This function checks if a file is on the ignore list, or not
def check_ignore(source):
    for f in ["InterrogateModule.cpp", "InterrogateWrapper.cpp"]:
        if f.lower() in source.lower():
            return False
    return True

# Collects all header files recursively
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

def execute(command):    
    if VERBOSE:
        with subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
            for line in p.stdout:
                print(line, end='', file=sys.stderr)
            for line in p.stderr:
                print("STDERR: ", line, end='', file=sys.stderr)
    else:
        try:
            subprocess.check_output(command, stderr=sys.stderr)
        except subprocess.CalledProcessError as msg:
            print("Error executing interrogate command:", msg, msg.output, file=sys.stderr)
            sys.exit(1)


# Collect source files and convert them to a relative path
all_sources = find_sources("Source/")
all_sources = [i.replace("Source/", "") for i in all_sources]

# Create interrogate command
if USE_ABS_PATH:
    cmd = [PANDA_BIN + '/interrogate']
else:
    cmd = ['interrogate']

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

if VERBOSE:
    cmd += ["-v"]

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
# cmd += ["config_rsnative.h"]q

# try:
#     subprocess.check_output(cmd, stderr=sys.stderr)
# except subprocess.CalledProcessError as msg:
#     print("Error executing interrogate command:", msg, msg.output, file=sys.stderr)
#     sys.exit(1)
execute(cmd)


# Create module command
if USE_ABS_PATH:
    cmd = [PANDA_BIN + '/interrogate_module']
else:
    cmd = ['interrogate_module']

cmd += ["-python-native"]
cmd += ["-import", "panda3d.core"] 
cmd += ["-module", MODULE_NAME] 
cmd += ["-library", MODULE_NAME] 
cmd += ["-oc", "Source/InterrogateModule.cpp"] 
cmd += ["Source/Interrogate.in"]

# try:
#     subprocess.check_output(cmd, stderr=sys.stderr)
# except subprocess.CalledProcessError as msg:
#     print("Error executing interrogate_module command: ", msg.output, file=sys.stderr)
#     sys.exit(1)

execute(cmd)



sys.exit(0)