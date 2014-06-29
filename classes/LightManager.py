
from DebugObject import DebugObject
from panda3d.core import PTAMat4, Shader
# from FastText import FastText

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

        self.lightsVisibleDebugText = None

        # todo
        self.shadowScene = render
    
                
        # Debug text to show how many lights are currently visible
        try:
            from FastText import FastText
            self.lightsVisibleDebugText = FastText()
            self.lightsVisibleDebugText.setPos(base.getAspectRatio() - 0.1, 0.9)
            self.lightsVisibleDebugText.setRightAligned(True)
            self.lightsVisibleDebugText.setColor(1,0,0)
            self.lightsVisibleDebugText.setSize(0.04)
        except Exception, msg:
            self.debug("Could not load fast text:", msg)
            self.lightsVisibleDebugText = None


        self.computingNodes = []

    def addLight(self, light):
        # if len(self.lights) >= self.maxLights:
        #     self.error("Too many lights! You cannot attach any more")
        #     return False

        self.debug("Adding light",light,"with",light.getNumShadowSources(), "shadow source(s)")

        self.lights.append(light)

    def setLightingComputators(self, shaderNodes):
        self.computingNodes = shaderNodes

        for shaderNode in self.computingNodes:
            shaderNode.setShaderInput("lightData", self.dataVector)
            # shaderNode.setShaderInput("lightMatrices", self.smatVector)
            shaderNode.setShaderInput("lightCount", 0)


    def debugReloadShader(self):
        pass


    def setCullBounds(self, bounds):
        self.cullBounds = bounds

    def update(self):

        # return
        self.numVisibleLights = 0

        for index, light in enumerate(self.lights):

            if self.numVisibleLights >= self.maxVisibleLights:
                # too many lights
                # self.error(
                    # "Too many lights! Can't display more than", self.maxVisibleLights)
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
            # self.smatVector[self.numVisibleLights] = lightData.getProjMat()

            self.numVisibleLights += 1

        if self.lightsVisibleDebugText is not None:
            self.lightsVisibleDebugText.setText('Visible Lights: ' + str(self.numVisibleLights))


        for shaderNode in self.computingNodes:
            shaderNode.setShaderInput("lightCount", self.numVisibleLights)

