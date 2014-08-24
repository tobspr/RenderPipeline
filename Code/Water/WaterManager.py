

import sys
sys.path.insert(0, "../RenderPipeline/")

from panda3d.core import Texture, NodePath, ShaderAttrib, LVecBase2i, PTAFloat
from panda3d.core import Vec2

from Code.DebugObject import DebugObject
from Code.BetterShader import BetterShader
from Code.Globals import Globals
from WaterDisplacement import WaterDisplacement, OceanOptions


class WaterManager(DebugObject):

    """ Simple wrapper arround WaterDisplacement which combines 3 displacement
    maps into one, and also generates a normal map """

    def __init__(self):
        DebugObject.__init__(self, "WaterManager")
        self.options = OceanOptions()
        self.options.size = 256
        self.options.wind = Vec2(0,128)
        self.options.length = 4096.0
        self.options.normalizationFactor = 6000.0

        self.displX = WaterDisplacement(self.options, 454232)
        self.displY = WaterDisplacement(self.options, 738452)
        self.displZ = WaterDisplacement(self.options, 384534)

        self.displacementTex = Texture("Displacement")
        self.displacementTex.setup2dTexture(
            self.options.size, self.options.size,
            Texture.TFloat, Texture.FRgba16)

        self.normalTex = Texture("Normal")
        self.normalTex.setup2dTexture(
            self.options.size, self.options.size,
            Texture.TFloat, Texture.FRgba16)

        self.combineShader = BetterShader.loadCompute(
            "Shader/Water/Combine.compute")

        self.ptaTime = PTAFloat.emptyArray(1)

        self.combineNode = NodePath("Combine")
        self.combineNode.setShader(self.combineShader)
        self.combineNode.setShaderInput(
            "displacementX", self.displX.getDisplacementTexture())
        self.combineNode.setShaderInput(
            "displacementY", self.displY.getDisplacementTexture())
        self.combineNode.setShaderInput(
            "displacementZ", self.displZ.getDisplacementTexture())
        self.combineNode.setShaderInput("normalDest", self.normalTex)
        self.combineNode.setShaderInput(
            "displacementDest", self.displacementTex)
        self.combineNode.setShaderInput(
            "N", LVecBase2i(self.options.size))
        # Store only the shader attrib as this is way faster
        self.combineAttr = self.combineNode.getAttrib(ShaderAttrib)

    def setup(self):
        """ Setups the manager """
        self.displX.setup()
        self.displY.setup()
        self.displZ.setup()

        # Make all textures tile + Have a linear filter:
        for tex in [self.displacementTex, self.normalTex,
                    self.displX.getDisplacementTexture(),
                    self.displY.getDisplacementTexture(),
                    self.displZ.getDisplacementTexture()]:
            tex.setMinfilter(Texture.FTLinear)
            tex.setMagfilter(Texture.FTLinear)
            tex.setWrapU(Texture.WMRepeat)
            tex.setWrapV(Texture.WMRepeat)

    def getDisplacementTexture(self):
        """ Returns the displacement texture, storing the 3D Displacement in
        the RGB channels """
        return self.displacementTex

    def getNormalTexture(self):
        """ Returns the normal texture, storing the normal in world space in
        the RGB channels """
        return self.normalTex

    def update(self):
        """ Updates the displacement / normal map """
        self.ptaTime[0] = 500 + Globals.clock.getFrameTime() * self.options.timeShift
        self.displX.update(self.ptaTime[0])
        self.displY.update(self.ptaTime[0])
        self.displZ.update(self.ptaTime[0])

        # Execute the shader which combines the 3 displacement maps into
        # 1 displacement texture and 1 normal texture. We could use dFdx in
        # the fragment shader, however that gives no accurate results as
        # dFdx returns the same value for a 2x2 pixel block
        Globals.base.graphicsEngine.dispatch_compute(
            (self.options.size / 16,
             self.options.size / 16, 1), self.combineAttr,
            Globals.base.win.get_gsg())


if __name__ == "__main__":

    from panda3d.core import loadPrcFileData, PStatClient, CardMaker
    from panda3d.core import loadPrcFile, Mat4, LPoint2f

    from PlaneTools import generateChunk
    loadPrcFile("../RenderPipeline/Config/configuration.prc")
    loadPrcFileData("", """
        textures-power-2 none
        gl-finish #f
        sync-video #f
        win-size 900 900

        """)

    import direct.directbase.DirectStart

    Globals.load(base)

    manager = WaterManager()
    manager.setup()

    def updateTask(task):
        manager.update()
        return task.cont

    # cm = CardMaker("cm")
    # cm.setFrame(0, 900, 0, -900)
    # cm.setUvRange(LPoint2f(-2, -2), LPoint2f(2, 2))
    # cnZ = Globals.base.pixel2d.attachNewNode(cm.generate())
    # cnZ.setTexture(manager.getDisplacementTexture())
    # cnZ.setPos(0, 0, 0)

    waterElem = generateChunk(256, 1.0 / 32.0)
    waterElem.reparentTo(Globals.base.render)
    waterElem.setPos(0, 0, 0)
    waterElem.setShaderInput("displacement", manager.getDisplacementTexture())
    waterElem.setShaderInput("normal", manager.getNormalTexture())
    waterElem.setInstanceCount(16*16)

    def loadShader():
        print "Load Shader"
        waterShader = BetterShader.load("Shader/Water/WaterDebugVertex.glsl",
                                        "Shader/Water/WaterDebugFragment.glsl")
        waterElem.setShader(waterShader)
    loadShader()

    Globals.base.disableMouse()
    Globals.base.camera.setPos(5, 5, 5)
    Globals.base.camera.lookAt(0, 0, 0)
    Globals.base.camLens.setFov(60)
    Globals.base.camLens.setNearFar(0.1, 1000.0)
    mat = Mat4(Globals.base.camera.getMat())
    mat.invertInPlace()
    Globals.base.mouseInterfaceNode.setMat(mat)
    Globals.base.enableMouse()

    Globals.base.accept("f3", Globals.base.toggleWireframe)
    Globals.base.accept("r", loadShader)

    Globals.base.taskMgr.add(updateTask, "test")
    Globals.base.accept("1", PStatClient.connect)

    Globals.base.run()
