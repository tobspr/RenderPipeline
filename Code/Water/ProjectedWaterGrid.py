

from panda3d.core import OmniBoundingVolume, Texture, Mat4, SamplerState

from ..DebugObject import DebugObject
from ..Globals import Globals

from WaterManager import WaterManager

class ProjectedWaterGrid(DebugObject):

    def __init__(self, pipeline):
        DebugObject.__init__(self, "ProjectedWaterGrid")
        self.debug("Creating water grid")

        self.waterLevel = 0.0

        self.model = Globals.loader.loadModel("Data/InternalModels/ScreenSpaceGrid.bam")
        self.model.reparentTo(Globals.base.render)
        self.model.node().setFinal(True)
        self.model.node().setBounds(OmniBoundingVolume())
        self.model.setTwoSided(True)
        self.model.setShaderInput("waterHeight", self.waterLevel)
        self.model.setMat(Mat4.identMat())
        self.model.clearTransform()

        foam = Globals.loader.loadTexture("Data/Textures/WaterFoam.png")
        self.model.setShaderInput("waterFoam", foam)       

        self.manager = WaterManager()
        self.manager.setup()
        self.manager.update()
        
        self.model.setShaderInput("waterHeightfield", self.manager.getDisplacementTexture())       
        self.model.setShaderInput("waterNormal", self.manager.getNormalTexture())       

        # Set texture filter modes
        for tex in [foam, self.manager.getDisplacementTexture(), self.manager.getNormalTexture()]:
            tex.setWrapU(SamplerState.WMRepeat)
            tex.setWrapU(SamplerState.WMRepeat)
            tex.setMinfilter(SamplerState.FTLinearMipmapLinear)
            tex.setMagfilter(SamplerState.FTLinearMipmapLinear)

        self.pipeline = pipeline

        self.pipeline.setEffect(self.model, "Effects/Water/ProjectedWater.effect", {
            # "transparent": True,
            "castShadows": False
            # "tesselated": True
        })

        # pipeline.convertToPatches(self.model)
        pipeline.showbase.addTask(self.updateTask, "updateWater")


    def setWaterLevel(self, level):
        self.waterLevel = level
        self.model.setShaderInput("waterHeight", level)

    def updateTask(self, task):
        self.manager.update()
        return task.cont
