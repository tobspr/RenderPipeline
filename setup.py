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

from __future__ import print_function

# This setups the pipeline
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
sys.path.insert(0, "Code/External/six")

from six.moves import input

# Load and init colorama, used to color the output
from Code.External.Colorama import init as init_colorama
from Code.External.Colorama import Fore, Style
init_colorama()

# Load submodule downloader
from Code.Util.SubmoduleDownloader import SubmoduleDownloader

def color(string, col):
    """ Colors a string """
    return col + string + Style.RESET_ALL

def error(msg):
    """ Prints an error message and then exists the program """
    print(color("Setup failed: ", Fore.RED + Style.BRIGHT), msg)
    print("Please fix the errors and then rerun this file")
    sys.exit(0)

def print_step(title):
    """ Prints a new section """
    global CURRENT_STEP
    CURRENT_STEP += 1
    print("\n\n[", str(CURRENT_STEP).zfill(2), "] ", color(title, Fore.CYAN + Style.BRIGHT))

def exec_python_file(pth):
    """ Executes a python file and checks the return value """
    basedir = os.path.dirname(os.path.abspath(os.path.join(SETUP_DIR, pth))) + "/"
    print("\tRunning script:", pth)
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
            print("\tExtracting .gz file:", fname)
            try:
                with open(fullpath[:-3], 'wb') as dest, gzip.open(fullpath, 'rb') as src:
                    shutil.copyfileobj(src, dest)
            except IOError as msg:
                error("Failed to extract file '" + fname + "': " + str(msg))
        elif os.path.isdir(fullpath):
            extract_gz_files(fullpath)

def hint_repo_not_complete(missing):
    """ Shows a hint that the repository is not complete """
    print("Missing the", missing, "submodule!")
    print("Please checkout the whole repository, and also make sure you")
    print("did 'git submodule init' and 'git submodule update' if you use")
    print("a command line client! Notice that the 'Download ZIP' on github")
    print("does *NOT* include submodules. ")
    error(missing + " submodule missing")

def check_file_exists(fpath):
    """ Checks if the given file exists """
    return os.path.isfile(os.path.join(SETUP_DIR, fpath))

def hint_download_submodule(author, module, dest_pth):
    """ Asks the user to download a submodule """

    query = ("It appears the submodule '" + module + "' is missing! Most likely you "
             "used the 'Download ZIP' button or did not use 'git submodule init'. Do "
             "you want the setup to automatically download the submodule for you? (y/n):")

    if get_user_choice(query):
        SubmoduleDownloader.download_submodule(author, module, dest_pth, [])
    else:
        hint_repo_not_complete(module)

def check_repo_complete():
    """ Checks if the repository is complete """

    # Check if the render target submodule exists
    if not check_file_exists("Code/RenderTarget/RenderTarget.py"):
        hint_download_submodule("tobspr", "RenderTarget", "Code/RenderTarget/")

    # Check if the color space submodule exists
    if not check_file_exists("Shader/Includes/ColorSpaces/ColorSpaces.inc.glsl"):
        hint_download_submodule("tobspr", "GLSL-Color-Spaces", "Shader/Includes/ColorSpaces/")


def ask_download_samples():
    """ Asks the user if he wants to download the samples """
    query = "\nDo you want to download the Render Pipeline samples? (y/n):"

    if get_user_choice(query):
        print_step("Downloading samples (Might take a while, depending on your internet) ...")
        exec_python_file("Samples/download_samples.py")

def get_user_choice(query):
    """ Asks the user a boolean question """
    print("\n")
    query = color(query, Fore.GREEN + Style.BRIGHT) + " "

    while True:
        user_choice = str(raw_input(query)).strip().lower()

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
        print("")
        print(color("Could not find cmake!", Fore.RED + Style.BRIGHT))
        print("It seems that cmake is not installed on this system, or not on")
        print("your path. Please install cmake and make sure it is on your path.")
        print("You can ensure this by running 'cmake --version' in a command line.")
        print("Full error message:")
        print(msg)
        error("cmake missing")

if __name__ == "__main__":

    print("-" * 79)
    print("\nRender Pipeline Setup 1.1\n")
    print("-" * 79)

    print_step("Checking if the repo is complete ..")
    check_repo_complete()

    if not OPT_SKIP_NATIVE:

        query = ("The C++ modules of the pipeline are faster and produce better "
                 "results, but we will have to compile them. As alternative, "
                 "a Python fallback is used, which is slower and produces worse "
                 "results. Also not all plugins work with the python fallback "
                 "(e.g. PSSM). Do you want to use the C++ modules? (y/n):")

        # Dont install the c++ modules when using travis
        if not OPT_AUTO_INSTALL and get_user_choice(query):
            check_cmake()

            write_flag("Code/Native/use_cxx.flag", True)

            print_step("Downloading the module builder ...")
            exec_python_file("Code/Native/update_module_builder.py")

            print_step("Building the native code .. (This might take a while!)")
            exec_python_file("Code/Native/build.py")

        else:
            write_flag("Code/Native/use_cxx.flag", False)

    if not OPT_AUTO_INSTALL:
        print_step("Generating normal quantization textures ..")
        exec_python_file("Data/NormalQuantization/generate.py")

        print_step("Extracting .gz files ...")
        extract_gz_files(os.path.join(SETUP_DIR, "Data/"))

        print_step("Filtering default cubemap ..")
        exec_python_file("Data/DefaultCubemap/filter.py")

        print_step("Precomputing film grain .. ")
        exec_python_file("Data/PrecomputedGrain/generate.py")

        ask_download_samples()

    # -- Further setup code follows here --

    write_flag("Data/install.flag", True)

    print(color("\n\n-- Setup finished sucessfully! --", Fore.GREEN + Style.BRIGHT))
