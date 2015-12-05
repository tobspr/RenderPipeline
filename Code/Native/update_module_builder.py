"""

This script downloads and updates the module builder.

"""

from __future__ import print_function

SOURCE_URL = "https://github.com/tobspr/P3DModuleBuilder/archive/master.zip"
PREFIX = "P3DModuleBuilder-master/"

# Dont checkout all files
IGNORE_FILES = [
    "__init__.py",
    ".gitignore",
    "LICENSE",
    "README.md",
    "config.ini",
    "Source/config_module.cpp",
    "Source/config_module.h",
    "Source/ExampleClass.cpp",
    "Source/ExampleClass.h",
    "Source/ExampleClass.I",
]

import os
import sys
import urllib
import zipfile
import shutil

# Include cStringIO in case its available, since its faster
try: from cStringIO import StringIO
except: from StringIO import StringIO


if __name__ == "__main__":

    print("Downloading P3DModuleBuilder from github ...")
    print("Fetching:", SOURCE_URL)   

    # Download the zip
    try:
        usock = urllib.urlopen(SOURCE_URL)
        zip_data = usock.read()
        usock.close()
    except Exception as msg:
        print("ERROR: Could not fetch module builder! Reason:", msg, file=sys.stderr)
        sys.exit(2)

    # Extract the zip
    zip_ptr = StringIO(zip_data)

    try:
        zip_handle = zipfile.ZipFile(zip_ptr)
    except zipfile.BadZipfile:
        print("ERROR: Invalid zip file!", file=sys.stderr)
        sys.exit(3)

    if zip_handle.testzip() is not None:
        print("ERROR: Invalid zip file checksums!", file=sys.stderr)
        sys.exit(1)

    for fname in zip_handle.namelist():
        rel_name = fname.replace(PREFIX, "").strip()
        if not rel_name:
            continue

        rel_name = rel_name.replace("\\", "/")

        # Files
        if not rel_name.endswith("/"):
            if rel_name not in IGNORE_FILES:
                print("Writing", rel_name)
                with zip_handle.open(fname, "r") as source, open(rel_name, "wb") as dest:
                        shutil.copyfileobj(source, dest)
        # Directories
        else:
            if not os.path.isdir(rel_name):
                print("Creating", rel_name)
                os.makedirs(rel_name)
