
import sys
import collections

# Import different PyYaml versions depending on the used python version 
if sys.version_info < (3, 0):
    from .yaml_py2 import load as YAMLLoad
    from .yaml_py2 import YAMLError as YAMLError
    from .yaml_py2 import SafeLoader
else:
    from .yaml_py3 import load as YAMLLoad
    from .yaml_py3 import YAMLError as YAMLError
    from .yaml_py3 import SafeLoader

def YAMLEasyLoad(filename):
    """ This method is a wrapper arround YAMLLoad, and provides error checking """
    from direct.stdpy.file import open
    from ...Util.DebugObject import DebugObject

    try:
        with open(filename, "r") as handle:
            parsed_yaml = YAMLLoad(handle, Loader=SafeLoader)
    except IOError as msg:
        DebugObject.global_error("YAMLLoader", "Could not find or open file:", filename)
        DebugObject.global_error("YAMLLoader", msg)
        raise Exception("Failed to load YAML file: File not found")

    except YAMLError as msg:
        DebugObject.global_error("YAMLLoader", "Invalid yaml-syntax in file:", filename)
        DebugObject.global_error("YAMLLoader", msg)
        raise Exception("Failed to load YAML file: Invalid syntax")

    return parsed_yaml
