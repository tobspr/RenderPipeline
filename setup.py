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

# Setup script to install everything required to run the pipeline.

# pylint: skip-file
# flake8: noqa

from __future__ import print_function
import os
import sys
import subprocess
import webbrowser
import gzip
import shutil
import argparse

sys.dont_write_bytecode = True

DEVNULL = open(os.path.devnull, "w")
SETUP_DIR = os.path.dirname(os.path.realpath(__file__))
CURRENT_STEP = 0

os.chdir(SETUP_DIR)
sys.path.insert(0, ".")

from rplibs.six.moves import input # pylint: disable=import-error

# Load and init colorama, used to color the output
from rplibs.colorama import init as init_colorama
from rplibs.colorama import Fore, Style
init_colorama()

def parse_cmd_args():
    """ Parses the command line arguments """
    parser = argparse.ArgumentParser(description="Render Pipeline Setup")
    parser.add_argument(
        "--clean", help="Clean rebuild of the native modules", action="store_true")
    parser.add_argument(
        "--verbose", help="Output additional debug information", action="store_true")
    parser.add_argument(
        "--skip-update", help="Skip updating the module builder to avoid overriding changes", action="store_true")
    parser.add_argument(
        "--skip-native", help="Skip native module compilation", action="store_true")
    parser.add_argument(
        "--ci-build", help="Skip setup steps requiring gpu drivers, only for travis ci", action="store_true")
    return parser.parse_args()

CMD_ARGS = parse_cmd_args()

def color(string, col):
    """ Colors a string """
    return col + string + Style.RESET_ALL

def error(msg):
    """ Prints an error message and then exists the program """
    print("\n" + color("Setup failed:\t", Fore.RED + Style.BRIGHT), msg)
    print(color("\nPlease fix the above errors and then restart the setup.\n",
                Fore.RED + Style.BRIGHT))
    sys.exit(-1)

def print_step(title):
    """ Prints a new section """
    global CURRENT_STEP
    CURRENT_STEP += 1
    print("\n\n[", str(CURRENT_STEP).zfill(2), "] ", color(title, Fore.CYAN + Style.BRIGHT))

def ask_for_troubleshoot(url):
    if CMD_ARGS.ci_build:
        print("\nSETUP FAILED!")
        return
        
    if not url:
        print("\nSorry, no troubleshooting options are available.\n")
        return

    query = "\nIt seems the setup failed, do you want to open the troubleshooting page for this step? (y/n):"
    if get_user_choice(query):
        print("OK, opening", url,"\n")
        webbrowser.open(url, new=2)

def exec_python_file(pth, args=None, troubleshoot=None):
    """ Executes a python file and checks the return value """
    basedir = os.path.dirname(os.path.abspath(os.path.join(SETUP_DIR, pth))) + "/"
    print("\tRunning script:", Fore.YELLOW + Style.BRIGHT + pth + Style.RESET_ALL)
    pth = os.path.basename(pth)
    os.chdir(basedir)
    cmd = [sys.executable, "-B", pth] + (args or [])
    if CMD_ARGS.verbose:
        print("Executing", ' '.join(cmd))
        print("CWD is", basedir)
    try:
        output = subprocess.check_output(cmd, stderr=sys.stderr)
    except subprocess.CalledProcessError as msg:
        print(color("Failed to execute '" + pth + "'", Fore.YELLOW + Style.BRIGHT))
        print("Output:", msg, "\n", msg.output.decode("utf-8", errors="ignore"))
        ask_for_troubleshoot(troubleshoot)
        error("Python script didn't return properly!")
    except IOError as msg:
        print("Python script error:", msg)
        ask_for_troubleshoot(troubleshoot)
        error("Error during script execution")
    if CMD_ARGS.verbose:
        print(output.decode("utf-8", errors="ignore"))
    os.chdir(SETUP_DIR)

def extract_gz_files(pth):
    """ Extract all gz files in the given path recursively """
    files = os.listdir(pth)
    for fname in files:
        fullpath = os.path.join(pth, fname)
        if os.path.isfile(fullpath) and fname.endswith(".gz"):
            print("\tExtracting", fname)
            try:
                with open(fullpath[:-3], 'wb') as dest, gzip.open(fullpath, 'rb') as src:
                    shutil.copyfileobj(src, dest)
            except IOError as msg:
                error("Failed to extract file '" + fname + "': " + str(msg))
        elif os.path.isdir(fullpath):
            extract_gz_files(fullpath)

def check_file_exists(fpath):
    """ Checks if the given file exists """
    return os.path.isfile(os.path.join(SETUP_DIR, fpath))

def ask_download_samples():
    """ Asks the user if he wants to download the samples """
    query = "\nDo you want to download the Render Pipeline samples (~450MB)? (y/n):"

    if get_user_choice(query):
        print_step("Downloading samples (Might take a while, depending on your "
                   "internet connection) ...")
        exec_python_file("samples/download_samples.py")

def get_user_choice(query):
    """ Asks the user a boolean question """
    print("\n")
    query = color(query, Fore.GREEN + Style.BRIGHT) + " "

    while True:
        print(query, end="")
        user_choice = input().strip().lower()

        if user_choice in ["y", "yes", "1"]:
            return True

        if user_choice in ["n", "no", "0"]:
            return False

        print(color("Invalid input: '" + user_choice + "'", Fore.RED + Style.BRIGHT))

def write_flag(flag_location, flag_value):
    """ Writes a binary flag """
    flag_location = os.path.join(SETUP_DIR, flag_location)
    try:
        with open(flag_location, "w") as handle:
            handle.write("1" if flag_value else "0")
    except IOError as msg:
        error("Failed to write flag to "+ flag_location + ", reason: " + str(msg))

def check_cmake():
    """ Checks if cmake is installed """
    try:
        subprocess.call(["cmake", "--version"], stdout=subprocess.PIPE)
    except Exception as msg:
        print("\n")
        print(color("Could not find cmake!", Fore.RED + Style.BRIGHT))
        print("It seems that cmake is not installed on this system, or not on")
        print("your path. Please install cmake and make sure it is on your path.")
        print("You can ensure this by running 'cmake --version' in a command line.")
        print("Full error message:")
        print(msg)
        error("cmake missing")

def check_panda_version():
    """ Checks whether the Panda3D version used is up to date. This is important
    when using the C++ modules """

    from panda3d.core import Texture

    if not hasattr(Texture, "F_r16i"):
        print("\n")
        print("It seems your Panda3D version is outdated. Please get the newest version ")
        print("from", color("https://github.com/panda3d/panda3d", Fore.MAGENTA + Style.BRIGHT),
              "(you can also build from source).")
        error("Panda3D version outdated")

def check_panda_rplight():
    """ Checks whether Panda3D provides the rpcore native module. """

    try:
        from panda3d import _rplight
        return True
    except ImportError:
        pass

    return False

def setup():
    """ Main setup routine """

    print("-" * 79)
    print("\nRender Pipeline Setup 1.3\n")
    print("-" * 79)


    if CMD_ARGS.ci_build:
        print()
        print(color("Running CI setup without steps requiring a GPU", Fore.BLUE + Style.BRIGHT))

    print_step("Checking Panda3D Modules")
    # Make sure this python build is using Panda3D
    try:
        from panda3d.core import NodePath
    except ImportError:
        print("\n")
        print("Could not import Panda3D modules! Please make sure they are ")
        print("on your path, and you are using the correct python version!")
        error("Failed to import Panda3D modules")

    check_panda_version()

    if not CMD_ARGS.ci_build:
        print_step("Checking requirements ..")
        exec_python_file("data/setup/check_requirements.py",
            troubleshoot="https://github.com/tobspr/RenderPipeline/wiki/Setup-Troubleshooting#requirements-check")

    if check_panda_rplight():
        write_flag("rpcore/native/use_cxx.flag", True)

    elif not CMD_ARGS.skip_native:
        query = ("The C++ modules of the pipeline are faster and produce better \n"
                 "results, but we will have to compile them. As alternative, \n"
                 "a Python fallback is used, which is slower and produces worse \n"
                 "results. Also some plugins only partially work with the python \n"
                 "fallback (e.g. PSSM). Do you want to compile the C++ modules? (y/n):")

        # Dont install the c++ modules when using travis
        if CMD_ARGS.ci_build or get_user_choice(query):
            check_cmake()
            write_flag("rpcore/native/use_cxx.flag", True)

            if not CMD_ARGS.skip_update:
                print_step("Downloading the module builder ...")
                exec_python_file("rpcore/native/update_module_builder.py",
                    troubleshoot="https://github.com/tobspr/RenderPipeline/wiki/Setup-Troubleshooting#downloading-module-builder")

            print_step("Building the native code .. (This might take a while!)")
            exec_python_file("rpcore/native/build.py", ["--clean"] if CMD_ARGS.clean else [],
                troubleshoot="https://github.com/tobspr/RenderPipeline/wiki/Setup-Troubleshooting#building-the-native-code")

        else:
            write_flag("rpcore/native/use_cxx.flag", False)

    print_step("Generating .txo files ...")
    exec_python_file("data/generate_txo_files.py",
        troubleshoot="https://github.com/tobspr/RenderPipeline/wiki/Setup-Troubleshooting#extracting-txo-files")

    if not CMD_ARGS.ci_build:
        print_step("Filtering default cubemap ..")
        exec_python_file("data/default_cubemap/filter.py",
            troubleshoot="https://github.com/tobspr/RenderPipeline/wiki/Setup-Troubleshooting#filtering-default-cubemap")

        print_step("Precomputing film grain .. ")
        exec_python_file("data/film_grain/generate.py",
            troubleshoot="https://github.com/tobspr/RenderPipeline/wiki/Setup-Troubleshooting#precomputing-film-grain")

    print_step("Running shader scripts .. ")
    exec_python_file("rpplugins/env_probes/shader/generate_mip_shaders.py",
        troubleshoot="https://github.com/tobspr/RenderPipeline/wiki/Setup-Troubleshooting#running-shader-scripts")


    if not CMD_ARGS.ci_build:
        print_step("Precomputing clouds ..")
        exec_python_file("rpplugins/clouds/resources/precompute.py",
            troubleshoot="https://github.com/tobspr/RenderPipeline/wiki/Setup-Troubleshooting#precomputing-clouds")

    write_flag("data/install.flag", True)

    # -- Further setup code follows here --

    print(color("\n\n-- Setup finished sucessfully! --", Fore.GREEN + Style.BRIGHT))

    if not CMD_ARGS.ci_build:
        ask_download_samples()


if __name__ == "__main__":
    setup()
