

# This script just copies the generated .pyd file to the current directory.

from shutil import copyfile
from os.path import isfile

source_file = None

possible_files = [
    "Windows/Release/RSNative.pyd",
    "Windows/x64/Release/RSNative.pyd",
]

for file in possible_files:
    if isfile(file):
        source_file = file

if source_file:
    copyfile(source_file, "RSNative.pyd")

