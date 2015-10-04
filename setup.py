

# This setups the pipeline
import os
import sys
import subprocess
import io
import gzip
import shutil

devnull = open(os.path.devnull, "w")
setup_dir = os.path.dirname(os.path.realpath(__file__))
current_step = 0



def error(msg):
    print "ERROR: ", msg
    print "The installation failed!"
    sys.exit(0)


def print_step(title):
    global current_step
    current_step += 1
    print "\n\n[", current_step, "]", title


def exec_python_file(pth):
    basedir = os.path.dirname(os.path.abspath(os.path.join(setup_dir, pth)))
    print "\tRunning script:", pth
    try:
        os.chdir(basedir)
        output = subprocess.check_output(["ppython", "-B", os.path.basename(pth)], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, msg:
        print "Python script didn't return properly:"
        print msg
        error("Failed to execute '" + pth + "'")

    except Exception, msg:
        print "Python script error:", msg
        error("Error during script execution")


def extract_gz_files(pth):
    pth = os.path.join(setup_dir, pth)
    files = os.listdir(pth)
    for f in files:
        fullpath = os.path.join(pth, f)
        if os.path.isfile(fullpath) and f.endswith(".gz"):
            print "\tExtracting .gz file:", f

            try:
                with open(fullpath[:-3], 'wb') as dest, gzip.open(fullpath, 'rb') as src:
                    shutil.copyfileobj(src, dest)
            except Exception, msg:
                error("Failed to extract file '" + f + "': " + str(msg))

print "\nRender Pipeline Setup 1.0\n"
print "-" * 79
print_step("Checking if ppython is on your path")

try:
    subprocess.call(["ppython", "--version"], stdout=devnull, stderr=devnull)
except OSError:
    error("Could not find ppython on your path")

print_step("Generating normal quantization textures")
exec_python_file("Data/NormalQuantization/generate.py")


print_step("Extracting .gz files ...")
extract_gz_files("Data/BuiltinModels/")


# Further setup code follows here

print "\n\n-- Setup finished! --"
