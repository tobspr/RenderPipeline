from __future__ import print_function

# This script prints out the location of the Panda3D sdk

import os
import sys
import panda3d

def get_sdk_path():
    pp = os.path.join(os.path.dirname(panda3d.__file__), "..\\")
    pp = os.path.abspath(pp).rstrip("/")
    return pp

if __name__ == "__main__":
    sys.stdout.write(get_sdk_path())
