

# This setups the pipeline
import os
import sys
import subprocess

devnull = open(os.path.devnull, "w")
setup_dir = os.path.dirname(os.path.realpath(__file__))


def error(msg):
    print "ERROR: ", msg
    print "The installation failed!"
    sys.exit(0)


def exec_python_file(pth):
    basedir = os.path.dirname(os.path.abspath(os.path.join(setup_dir, pth)))
    print "  Running script:", pth
    try:
        os.chdir(basedir)
        subprocess.call(["ppython", "-B", os.path.basename(pth)], stdout=devnull,
                        stderr=devnull)
        pass
    except Exception, msg:
        print "Failed to execute python script"
        print "Script: ", pth
        print "Message: ", msg
        error("Error during script execution")

print "\n\nRender Pipeline Setup 1.0\n\n"

print "[1] Checking if ppython is on your path"

try:
    subprocess.call(["ppython", "--version"], stdout=devnull, stderr=devnull)
except OSError:
    error("Could not find ppython on your path")

print "[2] Generating normal quantization textures"
exec_python_file("Data/NormalQuantization/generate.py")


print "Setup finished!"
