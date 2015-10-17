

# This script just copies the generated .pyd file to the current directory.

import platform
from shutil import copyfile
from os.path import isfile
source_file = None


if platform.system() == "Windows":
    possible_files = [
        "Windows/Release/RSNative.pyd",
        "Windows/x64/Release/RSNative.pyd",
    ]
    target_location = "RSNative.pyd"
elif platform.system() == "Linux":
    possible_files = [
        "Linux/RSNative.so"
    ]
    target_location = "RSNative.so"

for file in possible_files:
    if isfile(file):
        source_file = file

if source_file:
    copyfile(source_file, target_file)

