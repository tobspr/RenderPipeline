
from __future__ import print_function

import sys
sys.path.insert(0, "../")

# This file is just a container for all classes, so plugins can import this file
# and get all other class definitions required for plugins

from Code.PluginInterface.BasePlugin import BasePlugin
from Code.PluginInterface.PluginHook import PluginHook
from Code.PluginInterface.PluginSettings import PluginSettingInt, PluginSettingFloat, PluginSettingEnum
from Code.Util.Image import Image
from Code.RenderStage import RenderStage
from Code.RenderTarget import RenderTarget
from Code.Globals import Globals
from Code.Stages import *


def get_internal_stage_handle(module):
    """ Returns a stage handle by a given module, e.g.:
    get_stage_handle(AmbientStage).do_sth() """
    clsname = module.__name__.split(".")[-1]
    return getattr(module, clsname)
