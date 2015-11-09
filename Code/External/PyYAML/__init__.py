
import sys

# Import different PyYaml versions depending on the used python version 
if sys.version_info < (3, 0):
    from .yaml_py2 import load as YAMLLoad
    from .yaml_py2 import YAMLError as YAMLError
else:
    from .yaml_py3 import load as YAMLLoad
    from .yaml_py3 import YAMLError as YAMLError
