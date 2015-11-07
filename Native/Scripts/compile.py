from __future__ import print_function

import platform
import subprocess
import sys

from os import system, chdir, remove
from os.path import isfile, dirname, realpath, join


NATIVE_SRC = join(dirname(realpath(__file__)), "..")
SOLUTION_PATH = join(NATIVE_SRC, "Windows/RSNative.sln")


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

        devenv_pth = join(str(vc_versions[vc_version]), "Common7/IDE/devenv.exe")

        if not isfile(devenv_pth):
            print("devenv.exe not found! Expected it at:", devenv_pth, file=sys.stderr)
            return hint_manually_msvc()

        target_logfile = join(NATIVE_SRC, "compilation_log.txt")

        try:
            output = subprocess.check_output([devenv_pth, SOLUTION_PATH, "/build", "Release", "/projectconfig", "Release", "/out", target_logfile], stderr=sys.stderr)
        except subprocess.CalledProcessError as msg:

            # Check if a compilation log was generated
            if isfile(target_logfile):
                
                # Read in compilation file and output it
                with open(target_logfile, "r") as handle:
                    for line in handle.readlines():
                        print(line.strip(), file=sys.stderr)     

                # Delete the logfile afterwards
                try:
                    remove(target_logfile)
                except Exception as msg:
                    pass

                print("Compilation failed!", msg, msg.output, file=sys.stderr)
            else:
                print("Unkown Compilation-Error:", msg, msg.output, file=sys.stderr)
            return hint_manually_msvc()


        # Delete the logfile afterwards
        try:
            remove(target_logfile)
        except Exception as msg:
            pass


        print("Success!")
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
