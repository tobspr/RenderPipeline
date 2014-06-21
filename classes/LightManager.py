
from DebugObject import DebugObject

class LightManager(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "LightManager")
        self.maxLights = 256 
        self.lights = []
    
    def addLight(self, light):
        if len(self.lights) >= self.maxLights:
            self.error("Too many lights! You cannot attach any more")
            return False
        self.lights.append(light)

    def update(self):

        for light in self.lights:
            if light.needsUpdate():
                # self.debug("Updating light",light)
                light.performUpdate()

            if light.needsShadowUpdate():
                # self.debug("Updating shadow for light",light)
                light.performShadowUpdate()
