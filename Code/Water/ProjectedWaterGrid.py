

from panda3d.core import OmniBoundingVolume, Texture, Mat4

from ..DebugObject import DebugObject
from ..Globals import Globals

from WaterManager import WaterManager

class ProjectedWaterGrid(DebugObject):

    def __init__(self, pipeline):
        DebugObject.__init__(self, "ProjectedWaterGrid")
        self.debug("Creating water grid")

        self.waterLevel = -2.0

        self.model = Globals.loader.loadModel("Data/InternalModels/ScreenSpaceGrid.bam")
        self.model.reparentTo(Globals.base.render)
        self.model.node().setFinal(True)
        self.model.node().setBounds(OmniBoundingVolume())
        self.model.setTwoSided(True)
        self.model.setShaderInput("waterHeight", self.waterLevel)

        # safe is safe
        self.model.setMat(Mat4.identMat())
        self.model.clearTransform()

        foam = Globals.loader.loadTexture("Data/Textures/WaterFoam.png")
        foam.setWrapU(Texture.WMRepeat)        
        foam.setWrapV(Texture.WMRepeat)
        self.model.setShaderInput("waterFoam", foam)       
        
        # nmap = Globals.loader.loadTexture("Data/Textures/DefaultWaterNormal.png")
        # nmap.setWrapU(Texture.WMRepeat)        
        # nmap.setWrapV(Texture.WMRepeat)
        # self.model.setShaderInput("waterNormal", nmap)       


        self.manager = WaterManager()
        self.manager.setup()
        self.manager.update()

        
        self.model.setShaderInput("waterHeightfield", self.manager.getDisplacementTexture())       
        self.model.setShaderInput("waterNormal", self.manager.getNormalTexture())       


        self.pipeline = pipeline

        self.pipeline.setEffect(self.model, "Effects/Water/ProjectedWater.effect", {
            # "transparent": True,
            "castShadows": False
            # "tesselated": True
        })

        pipeline.convertToPatches(self.model)
        pipeline.showbase.addTask(self.updateTask, "updateWater")

    def updateTask(self, task):
        self.manager.update()
        return task.cont
