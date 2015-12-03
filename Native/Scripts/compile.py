from __future__ import print_function

import platform
import subprocess
import sys

from os import system, chdir, remove
from os.path import isfile, dirname, realpath, join

from panda3d.core import PandaSystem

IS_WIN_64 = PandaSystem.getPlatform() == "win_amd64"
NATIVE_SRC = join(dirname(realpath(__file__)), "..")
SOLUTION_PATH = join(NATIVE_SRC, "Windows_x" + ("64" if IS_WIN_64 else "32") + "/RSNative.sln")


def hint_manually_msvc():
    print("Could not automatically compile the project! Please head over to", file=sys.stderr)
    print("Native/Windows/ and compile the solution RSNative.sln in release mode!", file=sys.stderr)
    sys.exit(1)


def do_compile():
    print("Trying to compile the solution ..")

    if platform.system() == "Windows":

        # Find used visual studio version
        from vc_api import get_installed_vc_versions
        vc_versions = get_installed_vc_versions()

        vc_version = None

        if "10.0" in vc_versions:
            vc_version = "10.0"
        
        elif len(vc_versions.keys()) > 0:
            # Use highest possible version
            vc_version = list(sorted(vc_versions.keys()))[-1]
            print("WARNING: Could not find Visual Studio 2010. Using highest available", file=sys.stderr)
            print("Visual Studio Version (" + vc_version + ").", file=sys.stderr)

        if vc_version is None:
            print("No installed Visual Studio version found!", file=sys.stderr)
            return hint_manually_msvc()


        vc_path = join(str(vc_versions[vc_version]), "Common7/IDE/")
        cl_path = None

        for cl_name in ["devenv.exe", "vcexpress.exe"]:
            if isfile(join(vc_path, cl_name)):
                cl_path = join(vc_path, cl_name)
                break

        if cl_path is None:
            print("Could not find appropriate compiler! Expected either devenv.exe "
                  "or vcexpress.exe at: " + vc_path, file=sys.stderr)
            return hint_manually_msvc()

        target_logfile = join(NATIVE_SRC, "compilation_log.txt")

        # Remove old logfile content
        try:
            remove(target_logfile)
        except IOError: 
            pass

        try:
            output = subprocess.check_output([cl_path, SOLUTION_PATH, "/build", "Release", "/projectconfig", "Release", "/out", target_logfile], stderr=sys.stderr)
        except subprocess.CalledProcessError as msg:

            # Check if a compilation log was generated
            if isfile(target_logfile):
                
                # Read in compilation file and output it
                with open(target_logfile, "r") as handle:
                    for line in handle.readlines():
                        print(line.strip(), file=sys.stderr)     

                print("Compilation failed!", msg, msg.output, file=sys.stderr)
            else:
                print("Unkown Compilation-Error:", msg, msg.output, file=sys.stderr)
            return hint_manually_msvc()

        print("Success!", file=sys.stderr)
        sys.exit(0)

    elif platform.system() == "Linux":
        
        target_path = join(NATIVE_SRC, "Linux")
        chdir(target_path)
        
        try:
            output = subprocess.check_output(["make"], stderr=sys.stderr)
        except subprocess.CalledProcessError as msg:
            print("make failed:", msg.output, file=sys.stderr)
            sys.exit(1)

    else:
        error("Unsupported platform!")

do_compile()
