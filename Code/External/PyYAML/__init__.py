

import sys


# Import different PyYaml versions depending on the python version 
if sys.version_info < (3, 0):
    from .yaml_py2 import *
else:
    from .yaml_py3 import *
