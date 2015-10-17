from __future__ import print_function

import sys
import platform
from os import system, getcwd, listdir
from direct.stdpy.file import join, isfile
import subprocess


if len(sys.argv) != 4:
    print("Invalid arguments!")
    print("Arguments must be: [panda-bin] [panda-libs] [panda-include]")
    sys.exit(0)

# Parameters
PANDA_BIN = sys.argv[1]
PANDA_LIBS = sys.argv[2]
PANDA_INCLUDE = sys.argv[3]
MODULE_NAME = "RSNative"


COMPILER="MSVC" if platform.system() == "Windows" else "GCC"
IS_64_BIT=sys.maxsize > 2 ** 32



cwd = getcwd().replace("\\", "/").rstrip("/")

ignoreFiles = ["InterrogateModule.cpp", "InterrogateWrapper.cpp"]

def checkIgnore(source):
    for f in ignoreFiles:
        if f.lower() in source.lower():
            return False
    return True

allSources = [i for i in listdir("Source") if isfile(join("Source", i)) and checkIgnore(i) and i.endswith(".h") ]
allSourcesStr = ' '.join(['"' + i + '"' for i in allSources])


# interrogate -v -srcdir panda/src/express -Ipanda/src/express -D CPPPARSER -D __STDC__=1 -D __cplusplus=201103L -D _X86_ -D WIN32_VC -D WIN32 -D _WIN32 -D WIN64_VC -D WIN64 -D _WIN64 -D _MSC_VER=1600 -D "__declspec(param)=" -D __cdecl -D _near -D _far -D __near -D __far -D __stdcall -oc built_x64_buffered/tmp/libp3express_igate.cxx -od built_x64_buffered/pandac/input/libp3express.in -fnames -string -refcount -assert -python-native -Sbuilt_x64_buffered/include/parser-inc -Ipanda/src/express -Sbuilt_x64_buffered/tmp -Sbuilt_x64_buffered/include -Sthirdparty/win-python-x64/include -Sthirdparty/win-libs-vc10-x64/zlib/include -Sthirdparty/win-libs-vc10-x64/openssl/include -Sthirdparty/win-libs-vc10-x64/extras/include -module panda3d.core -library libp3express buffer.h checksumHashGenerator.h circBuffer.h compress_string.h config_express.h copy_stream.h datagram.h datagramGenerator.h datagramIterator.h datagramSink.h dcast.h encrypt_string.h error_




# print("\nRunning interrogate ..")

cmd = '"' + PANDA_BIN + '/interrogate" '
cmd += "-fnames -string -refcount -assert -python-native "
cmd += "-S" + PANDA_INCLUDE + "/parser-inc "
cmd += "-S" + PANDA_INCLUDE + "/ "
cmd += "-I" + PANDA_BIN + "/include/ "
cmd += "-srcdir \"" + join(cwd, "Source") + "\" "
cmd += "-oc Source/InterrogateWrapper.cpp "
cmd += "-od Source/Interrogate.in "
cmd += "-module " + MODULE_NAME + " "
cmd += "-library " + MODULE_NAME + " "
cmd += "-nomangle "

# Defines required to parse the panda source
defines = ["CPPPARSER", "__STDC__=1", "__cplusplus=201103L"]

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
    cmd += "-D" + define + " "
cmd += allSourcesStr

try:
    subprocess.call(cmd, shell=True)
except Exception as msg:
    print("Error executing interrogate command:", msg, file=sys.stderr)
    sys.exit(1)



# print("\nRunning interrogate_module ..")
cmd = PANDA_BIN + "/interrogate_module "
cmd += "-python-native " 
cmd += "-import panda3d.core " 
cmd += "-module " + MODULE_NAME + " " 
cmd += "-library " + MODULE_NAME + " " 
cmd += "-oc Source/InterrogateModule.cpp " 
cmd += "Source/Interrogate.in " 

try:
    subprocess.call(cmd, shell=True)
except Exception as msg:
    print("Error executing interrogate_module command: ", msg, file=sys.stderr)
    sys.exit(1)
