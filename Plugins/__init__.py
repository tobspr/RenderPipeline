

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


# Import all stages as a module, this is used for the get_internal_stage_handle
from Code.Stages import *

# The native module defines the includes in its own __init__ file, so this is okay
from Code.Native import *


def get_internal_stage_handle(module):
    """ Returns a stage handle by a given module, e.g.:
    
    get_stage_handle(AmbientStage).method(). 

    This can be used to add additional input or pipe requirements to internal
    pipeline stages, in case custom code is inserted, for example:

    get_stage_handle(AmbientStage).add_pipe_requirement("MyPipe") 

    """
    clsname = module.__name__.split(".")[-1]
    return getattr(module, clsname)
