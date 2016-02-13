"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 	 	    	 	
"""
"""

Common functions for the build system

"""
from __future__ import print_function

import sys
import subprocess
import platform
from os.path import dirname, realpath, join, isdir, isfile
from os import makedirs
from sys import argv, stdout, stderr, exit
from panda3d.core import PandaSystem, Filename, ExecutionEnvironment

def get_output_name():
    """ Returns the name of the output dir, depending on the system architecture """
    return PandaSystem.getPlatform().lower() + "_py{}{}".format(
        sys.version_info.major, sys.version_info.minor)
    

def get_script_dir():
    """ Returns the name of the directory the scripts are located in """
    return dirname(realpath(__file__))


def get_basepath():
    """ Returns the basepath, based on the script dir """
    return join(get_script_dir(), "..")


def get_output_dir():
    """ Returns the output directory where CMake generates the build files into """
    return join(get_basepath(), get_output_name())


def get_panda_sdk_path():
    """ Returns the path of the panda3d sdk, under windows """
    # Import the base panda3d module
    import panda3d

    # Path of the module
    p3d_module = dirname(panda3d.__file__)
    p3d_sdk = join(p3d_module, "..")

    # Convert it to a valid filename
    fname = Filename.from_os_specific(p3d_sdk)
    fname.make_absolute()
    return fname.to_os_specific()


def get_panda_bin_path():
    """ Returns the path to the panda3d binaries """
    if is_windows():
        return first_existing_path([join(get_panda_sdk_path(), "bin")], "interrogate.exe")
    elif is_linux():
        libpath = get_panda_lib_path()
        search = [
            join(libpath, "../bin"),
            "/usr/bin",
            "/usr/local/bin",
        ]
        return first_existing_path(search, "interrogate")
    raise NotImplementedError("Unsupported OS")


def get_panda_lib_path():
    """ Returns the path to the panda3d libraries """
    if is_windows():
        return first_existing_path([join(get_panda_sdk_path(), "lib")], "libpanda.lib")
    elif is_linux():
        return dirname(ExecutionEnvironment.get_dtool_name())
    raise NotImplementedError("Unsupported OS")


def get_panda_include_path():
    """ Returns the path to the panda3d includes """
    if is_windows():
        return first_existing_path([join(get_panda_sdk_path(), "include")], "dtoolbase.h")
    elif is_linux():
        libpath = get_panda_lib_path()
        search = [
            join(libpath, "../include/"),
            "/usr/include/panda3d",
            "/usr/local/include/panda3d"
        ]
        return first_existing_path(search, "dtoolbase.h")
    raise NotImplementedError("Unsupported OS")


def first_existing_path(paths, required_file=None):
    """ Returns the first path out of a given list of paths which exists.
    If required_file is set, the path additionally has to contain the given
    filename """
    for pth in paths:
        if isdir(pth) and (required_file is None or isfile(join(pth, required_file))):
            return pth
    debug_out("No path out of the given list exists!")
    for pth in paths:
        debug_out("[-]", pth)
    fatal_error("Failed to match path")


def is_64_bit():
    """ Returns whether the build system is 64 bit (=True) or 32 bit (=False) """
    return PandaSystem.get_platform() in ["win_amd64"]


def is_windows():
    """ Returns whether the build system is windows """
    return platform.system().lower() == "windows"


def is_linux():
    """ Returns wheter the build system is linux """
    return platform.system().lower() == "linux"


def get_compiler_name():
    """ Returns the name of the used compiler, either 'MSC', 'GCC' or 'CLANG' """
    full_name = PandaSystem.get_compiler()
    compiler_name = full_name.split()[0]
    return compiler_name.upper()


def fatal_error(*args):
    """ Prints an error to stderr and then exits with a nonzero status code """
    print("\n\n[!] FATAL ERROR:", *args, file=stderr)
    exit(1)


def debug_out(*args):
    """ Prints a debug output string """
    print(*args)


def try_makedir(dirname):
    """ Tries to make the specified dir, but in case it fails it does nothing """
    debug_out("Creating directory", dirname)
    try:
        makedirs(dirname)
    except: pass

def try_execute(*args, **kwargs):
    """ Tries to execute the given process, if everything wents good, it just
    returns, otherwise it prints the output to stderr and exits with a nonzero
    status code """
    debug_out("Executing command: ", ' '.join(args), "\n")
    try:
        if "verbose" in kwargs and kwargs["verbose"]:
            process = subprocess.Popen(args)
            process.communicate()
            if process.returncode != 0:
                raise Exception("Return-Code: " + str(process.returncode))

        else:
            output = subprocess.check_output(args, bufsize=1, stderr=subprocess.STDOUT)
            debug_out("Process output: ")
            debug_out(output)
    except subprocess.CalledProcessError as msg:
        debug_out("Process error:")
        debug_out(msg.output)
        fatal_error("Subprocess returned no-zero statuscode!")


def join_abs(*args):
    """ Behaves like os.path.join, but replaces stuff like '/../' """
    joined = join(*args)
    fname = Filename.from_os_specific(joined)
    fname.make_absolute()
    return fname.to_os_generic()


def get_ini_conf(fname):
    """ Very simple .ini file reader, with no error checking """
    with open(fname, "r") as handle:
        return {i.split("=")[0].strip(): i.split("=")[-1].strip() for i in handle.readlines() if i.strip()}


def write_ini_conf(config, fname):
    """ Very simple .ini file writer, with no error checking """
    with open(fname, "w") as handle: 
        handle.write(''.join("{}={}\n".format(k,v) for k,v in sorted(config.items())))

if __name__ == "__main__":

    # Command line utiliies

    if len(argv) != 2:
        fatal_error("USAGE: ppython common.py <option>")

    if "--print-sdk-path" in argv:
        stdout.write(get_panda_sdk_path())
        exit(0)

    elif "--print-paths" in argv:
        debug_out("SDK-Path:", get_panda_sdk_path())
        debug_out("BIN-Path:", get_panda_bin_path())
        debug_out("LIB-Path:", get_panda_lib_path())
        debug_out("INC-Path:", get_panda_include_path())
        debug_out("Compiler:", get_compiler_name())

    else:
        fatal_error("Unkown options: ", ' '.join(argv[1:]))