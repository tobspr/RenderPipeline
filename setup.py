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

# Disable the warning about the global statement, its fine since this is a simple
# setup script
# pylint: disable=W0603

# Disable the warning about relative imports
# pylint: disable=W0403

from __future__ import print_function
import os
import sys
import subprocess
import gzip
import shutil

sys.dont_write_bytecode = True

DEVNULL = open(os.path.devnull, "w")
SETUP_DIR = os.path.dirname(os.path.realpath(__file__))
CURRENT_STEP = 0
OPT_SKIP_NATIVE = "--skip-native" in sys.argv
OPT_AUTO_INSTALL = "--auto-install" in sys.argv

os.chdir(SETUP_DIR)
sys.path.insert(0, ".")

from rplibs.six.moves import input

# Load and init colorama, used to color the output
if sys.version_info.major == 2:
    from rplibs.colorama import init as init_colorama
    from rplibs.colorama import Fore, Style
    init_colorama()
else:
    # Colorama seems not to work in Py3, work arround it
    class Dummy(object):
        def __getattr__(self, key):
            return ""
    Fore = Dummy()
    Style = Dummy()

def color(string, col):
    """ Colors a string """
    return col + string + Style.RESET_ALL

def error(msg):
    """ Prints an error message and then exists the program """
    print("\n" + color("Setup failed:\t", Fore.RED + Style.BRIGHT), msg)
    print(color("\nPlease fix the above errors and then restart the setup.\n",
                Fore.RED + Style.BRIGHT))
    sys.exit(0)

def print_step(title):
    """ Prints a new section """
    global CURRENT_STEP
    CURRENT_STEP += 1
    print("\n\n[", str(CURRENT_STEP).zfill(2), "] ", color(title, Fore.CYAN + Style.BRIGHT))

def exec_python_file(pth):
    """ Executes a python file and checks the return value """
    basedir = os.path.dirname(os.path.abspath(os.path.join(SETUP_DIR, pth))) + "/"
    print("\tRunning script:", Fore.YELLOW + Style.BRIGHT + pth + Style.RESET_ALL)
    pth = os.path.basename(pth)
    os.chdir(basedir)
    try:
        subprocess.check_output([sys.executable, "-B", pth], stderr=sys.stderr)
    except subprocess.CalledProcessError as msg:
        print(color("Failed to execute '" + pth + "'", Fore.YELLOW + Style.BRIGHT))
        print("Output:", msg, "\n", msg.output)
        error("Python script didn't return properly!")
    except IOError as msg:
        print("Python script error:", msg)
        error("Error during script execution")
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
    query = "\nDo you want to download the Render Pipeline samples? (y/n):"

    if get_user_choice(query):
        print_step("Downloading samples (Might take a while, depending on your "
                   "internet connection) ...")
        exec_python_file("samples/download_samples.py")

def get_user_choice(query):
    """ Asks the user a boolean question """
    print("\n")
    query = color(query, Fore.GREEN + Style.BRIGHT) + " "

    while True:
        user_choice = input(query).strip().lower()

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
    except subprocess.CalledProcessError as msg:
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

    from panda3d.core import PointLight

    if not hasattr(PointLight(""), "shadow_caster"):
        print("\n")
        print("It seems your Panda3D version is outdated. Please get the newest version ")
        print("from", color("https://github.com/panda3d/panda3d", Fore.MAGENTA + Style.BRIGHT),
              "(you have to build from source).")
        error("Panda3D version outdated")

def setup():
    """ Main setup routine """

    print("-" * 79)
    print("\nRender Pipeline Setup 1.1\n")
    print("-" * 79)

    print_step("Checking Panda3D Modules")
    # Make sure this python build is using panda3D
    try:
        from panda3d.core import NodePath
    except ImportError:
        print("\n")
        print("Could not import Panda3D modules! Please make sure they are ")
        print("on your path, and you are using the correct python version!")
        error("Failed to import Panda3D modules")

    check_panda_version()

    if not OPT_SKIP_NATIVE:
        query = ("The C++ modules of the pipeline are faster and produce better \n"
                 "results, but we will have to compile them. As alternative, \n"
                 "a Python fallback is used, which is slower and produces worse \n"
                 "results. Also some plugins only partially work with the python \n"
                 "fallback (e.g. PSSM). Do you want to compile the C++ modules? (y/n):")

        # Dont install the c++ modules when using travis
        if not OPT_AUTO_INSTALL and get_user_choice(query):
            check_cmake()

            write_flag("rpcore/native/use_cxx.flag", True)

            print_step("Downloading the module builder ...")
            exec_python_file("rpcore/native/update_module_builder.py")

            print_step("Building the native code .. (This might take a while!)")
            exec_python_file("rpcore/native/build.py")

        else:
            write_flag("rpcore/native/use_cxx.flag", False)

    if not OPT_AUTO_INSTALL:

        print_step("Extracting .gz files ...")
        extract_gz_files(os.path.join(SETUP_DIR, "data/"))

        print_step("Filtering default cubemap ..")
        exec_python_file("data/default_cubemap/filter.py")

        print_step("Precomputing film grain .. ")
        exec_python_file("data/film_grain/generate.py")

        print_step("Running shader scripts .. ")
        exec_python_file("rpplugins/env_probes/shader/generate_mip_shaders.py")

        print_step("Precomputing clouds ..")
        exec_python_file("rpplugins/clouds/resources/precompute.py")

        ask_download_samples()

    # -- Further setup code follows here --

    write_flag("data/install.flag", True)

    print(color("\n\n-- Setup finished sucessfully! --", Fore.GREEN + Style.BRIGHT))


if __name__ == "__main__":
    setup()
