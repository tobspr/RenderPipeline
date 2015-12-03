
# Disable import warnings from PyLint, it cannot find the modules since the
# render pipeline attaches the base path to the system path, which pylint is
# unable to detect.
# pylint: disable=F0401

# This file is just a container for all classes, so plugins can import this file
# and get all other class definitions required for plugins


# Add the pipeline code path to the system path, so we can include the pipeline
# classes. This is required because the plugins are not in the same package as
# the code.
import sys
sys.path.insert(0, "../")

# Include a subset of the pipeline classes and the plugin api
from Code.PluginInterface.BasePlugin import BasePlugin
from Code.PluginInterface.PluginHook import PluginHook, SettingChanged
from Code.Util.Image import Image
from Code.Util.DebugObject import DebugObject
from Code.Util.SliceLoader import SliceLoader
from Code.RenderStage import RenderStage
from Code.RenderTarget import RenderTarget
from Code.Globals import Globals


# Import all stages as a module, this is used for the get_internal_stage
from Code.Stages import *

# The native module defines the includes in its own __init__ file, so this is okay
from Code.Native import *


def get_internal_stage(module_name):
    """ Returns a stage handle by a given module, e.g.:

    get_internal_stage("AmbientStage").method().

    This can be used to add additional input or pipe requirements to internal
    pipeline stages, in case custom code is inserted, for example:

    get_internal_stage("AmbientStage").add_pipe_requirement("MyPipe")

    """
    handle = globals()[module_name]
    return getattr(handle, module_name)
