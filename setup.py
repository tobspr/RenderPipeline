

# This setups the pipeline
import os
import sys
import subprocess

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
        subprocess.call(["ppython", "-B", os.path.basename(pth)],
                        stdout=devnull,
                        stderr=devnull)
    except Exception, msg:
        print "Python script error:", msg
        error("Error during script execution")

print "\nRender Pipeline Setup 1.0\n"
print "-" * 79
print_step("Checking if ppython is on your path")

try:
    subprocess.call(["ppython", "--version"], stdout=devnull, stderr=devnull)
except OSError:
    error("Could not find ppython on your path")

print_step("Generating normal quantization textures")
exec_python_file("Data/NormalQuantization/generate.py")


# Further setup code follows here

print "\n\n-- Setup finished! --"
