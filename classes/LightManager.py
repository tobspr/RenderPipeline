
from DebugObject import DebugObject
from panda3d.core import PTAMat4
from FastText import FastText

from BetterShader import BetterShader

class LightManager(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "LightManager")
        self.maxVisibleLights = 64
        self.lights = []
        self.numVisibleLights = 0
        self.cullBounds = None

        self.dataVector = PTAMat4.empty_array(self.maxVisibleLights)
        self.smatVector = PTAMat4.empty_array(self.maxVisibleLights)

        # # Debug text to show how many lights are currently visible
        # self.lightsVisibleDebugText = FastText()
        # self.lightsVisibleDebugText.setPos(base.getAspectRatio() - 0.1, 0.9)
        # self.lightsVisibleDebugText.setRightAligned(True)
        # self.lightsVisibleDebugText.setColor(1,1,1)
        # self.lightsVisibleDebugText.setSize(0.04)


    def addLight(self, light):
        # if len(self.lights) >= self.maxLights:
        #     self.error("Too many lights! You cannot attach any more")
        #     return False
        self.lights.append(light)

    def setPipelineShader(self):
        pipelineShader = BetterShader.loadCompute("Shader/LightingPipeline.compute")
        
        if pipelineShader.getErrorFlag():
            print "Shader contains an error! Cannot set .."
        else:
            self.computeShaderNode.setShader(pipelineShader)


    def setComputeShaderNode(self, computeShader):
        self.computeShaderNode = computeShader
        self.computeShaderNode.setShaderInput("lightData", self.dataVector)
        self.computeShaderNode.setShaderInput("lightMatrices", self.smatVector)
        self.computeShaderNode.setShaderInput("lightCount", 0)
        self.setPipelineShader()

    def debugReloadShader(self):
        self.setPipelineShader()


    def setCullBounds(self, bounds):
        self.cullBounds = bounds

    def update(self):

        self.numVisibleLights = 0

        for index, light in enumerate(self.lights):

            if self.numVisibleLights >= self.maxVisibleLights:
                # too many lights
                self.error(
                    "Too many lights! Can't display more than", self.maxVisibleLights)
                break

            # update light if required
            if light.needsUpdate():
                light.performUpdate()

            # check if visible
            if not self.cullBounds.contains(light.getBounds()):
                continue

            if light.needsUpdate():
                # self.debug("Updating light",light)
                light.performUpdate()

            if light.needsShadowUpdate():
                # self.debug("Updating shadow for light",light)
                light.performShadowUpdate()

            # todo: visibility check
            lightData = light.getData()
            self.dataVector[self.numVisibleLights] = lightData.getDataMat()
            self.smatVector[self.numVisibleLights] = lightData.getProjMat()

            self.numVisibleLights += 1

        # self.lightsVisibleDebugText.setText('Visible Lights: ' + str(self.numVisibleLights))
        self.computeShaderNode.setShaderInput("lightCount", self.numVisibleLights)

