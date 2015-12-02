"""

Setup script to install everything required to run the pipeline.

"""

from __future__ import print_function

# This setups the pipeline
import os
import sys
import subprocess
import gzip
import shutil

sys.dont_write_bytecode = True


devnull = open(os.path.devnull, "w")
setup_dir = os.path.dirname(os.path.realpath(__file__))
current_step = 0
skip_native = len(sys.argv) > 1 and "--skip-native" in sys.argv


def error(msg):
    """ Prints an error message and then exists the program """
    print("Setup failed: ", msg)
    print("Please fix the errors and then rerun this file")
    sys.exit(0)


def print_step(title):
    """ Prints a new section """
    global current_step
    current_step += 1
    print("\n\n[", str(current_step).zfill(2), "] ", title)


def exec_python_file(pth):
    """ Executes a python file and checks the return value """
    basedir = os.path.dirname(os.path.abspath(os.path.join(setup_dir, pth))) + "/"
    print("\tRunning script:", pth)
    pth = os.path.basename(pth)
    os.chdir(basedir)
    try:
        subprocess.check_output([sys.executable, "-B", pth], stderr=sys.stderr)
    except subprocess.CalledProcessError as msg:
        print("Python script didn't return properly!")
        error("Failed to execute '" + pth + "'")
    except Exception as msg:
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
    return os.path.isfile(os.path.join(setup_dir, fpath))

def check_repo_complete():
    """ Checks if the repository is complete """

    # Check if the render target submodule exists
    if not check_file_exists("Code/RenderTarget/RenderTarget.py"):
        hint_repo_not_complete("RenderTarget")

    # Check if the color space submodule exists
    if not check_file_exists("Shader/Includes/ColorSpaces/ColorSpaces.inc.glsl"):
        hint_repo_not_complete("GLSLColorSpaces")


if __name__ == "__main__":

    print("\nRender Pipeline Setup 1.0\n")
    print("-" * 79)

    print_step("Checking if the repo is complete ..")
    check_repo_complete()

    if not skip_native:
        print_step("Compiling the native code .. (This might take a while!)")
        exec_python_file("Native/Scripts/setup_native.py")

    print_step("Generating normal quantization textures ..")
    exec_python_file("Data/NormalQuantization/generate.py")

    print_step("Extracting .gz files ...")
    extract_gz_files(os.path.join(setup_dir, "Data/"))

    print_step("Filtering default cubemap ..")
    exec_python_file("Data/DefaultCubemap/filter.py")

    # Further setup code follows here

    # Write install flag
    with open(os.path.join(setup_dir, "Data/install.flag"), "w") as handle:
        handle.write("1")

    print("\n\n-- Setup finished sucessfully! --")
