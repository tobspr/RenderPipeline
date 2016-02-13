
import shutil
import sys
import multiprocessing
from os import chdir
from os.path import join, isdir
from panda3d.core import PandaSystem

from .common import *


def make_output_dir(clean=False):
    """ Creates the output directory and sets the CWD into that directory. If
    clean is True, the output dir will be cleaned up. """
    output_dir = get_output_dir()

    # Cleanup output directory in case clean is specified
    if isdir(output_dir) and clean:
        print("Cleaning up output directory ..")
        shutil.rmtree(output_dir)

    try_makedir(output_dir)
    if not isdir(output_dir):
        fatal_error("Could not create output directory at:", output_dir)
    chdir(output_dir)


def run_cmake(config, args):
    """ Runs cmake in the output dir """

    configuration = "Release"
    if config["generate_pdb"].lower() in ["1", "true", "yes", "y"]:
        configuration = "RelWithDebInfo"

    cmake_args = ["-DCMAKE_BUILD_TYPE=" + configuration]
    cmake_args += ["-DPYTHON_EXECUTABLE:STRING=" + sys.executable]
    cmake_args += ["-DPROJECT_NAME:STRING=" + config["module_name"]]

    lib_prefix = "lib" if is_windows() else ""

    # Check for the right interrogate lib
    if PandaSystem.get_major_version() > 1 or PandaSystem.get_minor_version() > 9:
        cmake_args += ["-DINTERROGATE_LIB:STRING=" + lib_prefix + "p3interrogatedb"]
    else:

        # Buildbot versions do not have the core lib, instead try using libpanda
        if not isfile(join_abs(get_panda_lib_path(), "core.lib")):
            cmake_args += ["-DINTERROGATE_LIB:STRING=" + lib_prefix + "panda"]
        else:
            cmake_args += ["-DINTERROGATE_LIB:STRING=core"]

    if is_windows():
        # Specify 64-bit compiler when using a 64 bit panda sdk build
        bit_suffix = " Win64" if is_64_bit() else ""
        cmake_args += ["-G" + config["vc_version"] + bit_suffix]


    # Specify python version, once as integer, once seperated by a dot
    pyver = "{}{}".format(sys.version_info.major, sys.version_info.minor)
    pyver_dot = "{}.{}".format(sys.version_info.major, sys.version_info.minor)

    if is_windows():
        cmake_args += ["-DPYTHONVER:STRING=" + pyver]

    if is_linux():
        cmake_args += ["-DPYTHONVERDOT:STRING=" + pyver_dot]

    # Libraries
    for lib in ["freetype", "bullet", "eigen"]:
        if "use_lib_" + lib in config and config["use_lib_" + lib] in ["1", "yes", "y"]:
            cmake_args += ["-DUSE_LIB_" + lib.upper() + "=TRUE"]

    # Optimization level
    optimize = 3
    if args.optimize is None:
        # No optimization level set. Try to find it in the config
        if "optimize" in config:
            optimize = config["optimize"]
    else:
        optimize = args.optimize

    # Verbose level
    if "verbose_igate" in config:
        cmake_args += ["-DIGATE_VERBOSE=" + str(config["verbose_igate"])]
    else:
        cmake_args += ["-DIGATE_VERBOSE=0"]

    cmake_args += ["-DOPTIMIZE=" + str(optimize)]

    try_execute("cmake", join_abs(get_script_dir(), ".."), *cmake_args)

def run_cmake_build(config, args):
    """ Runs the cmake build which builds the final output """

    configuration = "Release"
    if config["generate_pdb"].lower() in ["1", "true", "yes", "y"]:
        configuration = "RelWithDebInfo"

    # get number of cores
    num_cores = multiprocessing.cpu_count()

    core_option = ""
    if is_linux():
        # On linux, use all available cores
        core_option = "-j" + str(num_cores)
    if is_windows():
        # Specifying no cpu count makes MSBuild use all available ones
        core_option = "/m"


    try_execute("cmake", "--build", ".", "--config", configuration, "--", core_option)

