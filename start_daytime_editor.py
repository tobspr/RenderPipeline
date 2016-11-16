#!/usr/bin/env python

import os
import sys
import subprocess
this_dir = os.path.dirname(os.path.realpath(__file__))

if not os.path.isfile(os.path.join(this_dir, "data", "install.flag")):
    print("Please install the pipeline first by running setup.py")
    sys.exit(-1)
to_execute = os.path.join(this_dir, "toolkit", "day_time_editor", "main.py")
subprocess.call([sys.executable, to_execute])
