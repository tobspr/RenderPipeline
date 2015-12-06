"""

Setup script to install everything required to run the pipeline.

"""

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

def error(msg):
    """ Prints an error message and then exists the program """
    print("Setup failed: ", msg)
    print("Please fix the errors and then rerun this file")
    sys.exit(0)


def print_step(title):
    """ Prints a new section """
    global CURRENT_STEP
    CURRENT_STEP += 1
    print("\n\n[", str(CURRENT_STEP).zfill(2), "] ", title)


def exec_python_file(pth):
    """ Executes a python file and checks the return value """
    basedir = os.path.dirname(os.path.abspath(os.path.join(SETUP_DIR, pth))) + "/"
    print("\tRunning script:", pth)
    pth = os.path.basename(pth)
    os.chdir(basedir)
    try:
        subprocess.check_output([sys.executable, "-B", pth], stderr=sys.stderr)
    except subprocess.CalledProcessError as msg:
        print("Failed to execute '" + pth + "'")
        print("Output:", msg, "\n", msg.output)
        error("Python script didn't return properly!")
    except IOError as msg:
        print("Python script error:", msg)
        error("Error during script execution")

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
    print("-" * 79)
    print("  You didn't checkout the", missing, "submodule!")
    print("  Please checkout the whole repository, and also make sure you ")
    print("  did 'git submodule init' and 'git submodule update' if you use")
    print("  a command line client!")
    print("-" * 79)
    error(missing + " submodule missing")

def check_file_exists(fpath):
    """ Checks if the given file exists """
    return os.path.isfile(os.path.join(SETUP_DIR, fpath))

def check_repo_complete():
    """ Checks if the repository is complete """

    # Check if the render target submodule exists
    if not check_file_exists("Code/RenderTarget/RenderTarget.py"):
        hint_repo_not_complete("RenderTarget")

    # Check if the color space submodule exists
    if not check_file_exists("Shader/Includes/ColorSpaces/ColorSpaces.inc.glsl"):
        hint_repo_not_complete("GLSLColorSpaces")


def ask_download_samples():
    """ Asks the user if he wants to download the samples """
    query = "\nDo you want to download the Render Pipeline samples? (y/n): "
    
    if get_user_choice(query):
        print_step("Downloading samples ...")
        exec_python_file("Samples/download_samples.py")

def get_user_choice(query):
    """ Asks the user a boolean question """
    print("\n")
    if sys.version_info.major > 2:
        user_choice = str(input(query)).strip().lower()
    else:
        user_choice = str(raw_input(query)).strip().lower()
        
    if user_choice in ["y", "yes", "1"]:
        return True

    return False

if __name__ == "__main__":

    print("\nRender Pipeline Setup 1.1\n")
    print("-" * 79)

    print_step("Checking if the repo is complete ..")
    check_repo_complete()

    if not OPT_SKIP_NATIVE:

        query = ("The C++ modules of the pipeline are faster and produce better "
                 "results, but we will have to compile them. As alternative, "
                 "a Python fallback is used, which is slower and produces worse "
                 "results. Do you want to use the C++ modules? (y/n): ")

        if get_user_choice(query):
            print_step("Downloading the module builder ...")
            exec_python_file("Code/Native/update_module_builder.py")

            print_step("Building the native code .. (This might take a while!)")
            exec_python_file("Code/Native/build.py")

        else:
            print_step("Making python wrappers ...")
            exec_python_file("Code/Native/PythonImpl/make_python_impl.py")

    print_step("Generating normal quantization textures ..")
    exec_python_file("Data/NormalQuantization/generate.py")

    print_step("Extracting .gz files ...")
    extract_gz_files(os.path.join(SETUP_DIR, "Data/"))

    print_step("Filtering default cubemap ..")
    exec_python_file("Data/DefaultCubemap/filter.py")

    ask_download_samples()

    # Further setup code follows here

    # Write install flag
    with open(os.path.join(SETUP_DIR, "Data/install.flag"), "w") as handle:
        handle.write("1")

    print("\n\n-- Setup finished sucessfully! --")
