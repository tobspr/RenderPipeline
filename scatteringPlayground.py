# Don't generate that annoying .pyc files
import sys
sys.dont_write_bytecode = True

import math
import struct
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *

from classes.MovementController import MovementController
from classes.RenderingPipeline import RenderingPipeline
from classes.PointLight import PointLight
from classes.DirectionalLight import DirectionalLight
from classes.BetterShader import BetterShader
from classes.DebugObject import DebugObject
from classes.FirstPersonController import FirstPersonCamera
from classes.Scatttering import Scattering
from classes.Globals import Globals

class Main(ShowBase, DebugObject):

    """ This is the render pipeline testing showbase """

    def __init__(self):
        DebugObject.__init__(self, "Main")

        self.debug("Bitness =", 8 * struct.calcsize("P"))

        # Load engine configuration
        self.debug("Loading panda3d configuration from configuration.prc ..")
        loadPrcFile("configuration.prc")
        
        
        # Init the showbase
        ShowBase.__init__(self)

        # taskMgr.step()
        base.accept("v", base.bufferViewer.toggleEnable)

        Globals.load(self, ".")

        # Create scattering
        earth = Scattering()
        earth.setSettings({

            })
        earth.precompute()




app = Main()
app.run()
