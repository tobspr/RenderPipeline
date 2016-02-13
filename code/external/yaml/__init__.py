
import sys
import collections
from direct.stdpy.file import open
from ...rp_object import RPObject

# Import different PyYaml versions depending on the used python version
if sys.version_info < (3, 0):
    from .yaml_py2 import load as yaml_load
    from .yaml_py2 import YAMLError
    from .yaml_py2 import SafeLoader
else:
    from .yaml_py3 import load as yaml_load
    from .yaml_py3 import YAMLError
    from .yaml_py3 import SafeLoader

__all__ = ["load_yaml_file"]

def load_yaml_file(filename):
    """ This method is a wrapper arround yaml_load, and provides error checking """

    try:
        with open(filename, "r") as handle:
            parsed_yaml = yaml_load(handle, Loader=SafeLoader)
    except IOError as msg:
        RPObject.global_error("YAMLLoader", "Could not find or open file:", filename)
        RPObject.global_error("YAMLLoader", msg)
        raise Exception("Failed to load YAML file: File not found")
    except YAMLError as msg:
        RPObject.global_error("YAMLLoader", "Invalid yaml-syntax in file:", filename)
        RPObject.global_error("YAMLLoader", msg)
        raise Exception("Failed to load YAML file: Invalid syntax")

    return parsed_yaml
