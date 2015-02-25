

from panda3d.core import Texture, NodePath, ShaderAttrib, LVecBase2i, PTAFloat
from panda3d.core import Vec2, PNMImage, LVecBase3d

from Code.DebugObject import DebugObject
from Code.BetterShader import BetterShader
from Code.Globals import Globals
from GPUFFT import GPUFFT

from random import random as generateRandom
from random import seed as setRandomSeed

from math import sqrt, log, cos, pi


class OceanOptions:

    """ This class stores all options required for the WaterDisplacement """
    size = 128

    windDir = Vec2(0.8, 0.6)
    windSpeed = 600.0
    windDependency = 0.2
    choppyScale = 1.3
    patchLength = 2000.0
    waveAmplitude = 0.35

    timeScale = 0.8
    normalizationFactor = 150.0


class WaterManager(DebugObject):

    """ Simple wrapper arround WaterDisplacement which combines 3 displacement
    maps into one, and also generates a normal map """

    def __init__(self):
        DebugObject.__init__(self, "WaterManager")
        self.options = OceanOptions()
        self.options.size = 512
        self.options.windDir.normalize()
        self.options.waveAmplitude *= 1e-7

        self.displacementTex = Texture("Displacement")
        self.displacementTex.setup2dTexture(
            self.options.size, self.options.size,
            Texture.TFloat, Texture.FRgba16)

        self.normalTex = Texture("Normal")
        self.normalTex.setup2dTexture(
            self.options.size, self.options.size,
            Texture.TFloat, Texture.FRgba16)

        self.combineShader = BetterShader.loadCompute(
            "Water/Combine.compute")

        self.ptaTime = PTAFloat.emptyArray(1)

        # Create a gaussian random texture, as shaders aren't well suited
        # for that
        setRandomSeed(523)
        self.randomStorage = PNMImage(self.options.size, self.options.size, 4)
        self.randomStorage.setMaxval((2 ** 16) - 1)

        for x in xrange(self.options.size):
            for y in xrange(self.options.size):
                rand1 = self._getGaussianRandom() / 10.0 + 0.5
                rand2 = self._getGaussianRandom() / 10.0 + 0.5
                self.randomStorage.setXel(x, y, LVecBase3d(rand1, rand2, 0))
                self.randomStorage.setAlpha(x, y, 1.0)

        self.randomStorageTex = Texture("RandomStorage")
        self.randomStorageTex.load(self.randomStorage)
        self.randomStorageTex.setFormat(Texture.FRgba16)
        self.randomStorageTex.setMinfilter(Texture.FTNearest)
        self.randomStorageTex.setMagfilter(Texture.FTNearest)

        # Create the texture wwhere the intial height (H0 + Omega0) is stored.
        self.texInitialHeight = Texture("InitialHeight")
        self.texInitialHeight.setup2dTexture(
            self.options.size, self.options.size,
            Texture.TFloat, Texture.FRgba16)
        self.texInitialHeight.setMinfilter(Texture.FTNearest)
        self.texInitialHeight.setMagfilter(Texture.FTNearest)

        # Create the shader which populates the initial height texture
        self.shaderInitialHeight = BetterShader.loadCompute(
            "Water/InitialHeight.compute")
        self.nodeInitialHeight = NodePath("initialHeight")
        self.nodeInitialHeight.setShader(self.shaderInitialHeight)
        self.nodeInitialHeight.setShaderInput("dest", self.texInitialHeight)
        self.nodeInitialHeight.setShaderInput(
            "N", LVecBase2i(self.options.size))
        self.nodeInitialHeight.setShaderInput(
            "patchLength", self.options.patchLength)
        self.nodeInitialHeight.setShaderInput("windDir", self.options.windDir)
        self.nodeInitialHeight.setShaderInput(
            "windSpeed", self.options.windSpeed)
        self.nodeInitialHeight.setShaderInput(
            "waveAmplitude", self.options.waveAmplitude)
        self.nodeInitialHeight.setShaderInput(
            "windDependency", self.options.windDependency)
        self.nodeInitialHeight.setShaderInput(
            "randomTex", self.randomStorageTex)

        self.attrInitialHeight = self.nodeInitialHeight.getAttrib(ShaderAttrib)

        self.heightTextures = []
        for i in xrange(3):

            tex = Texture("Height")
            tex.setup2dTexture(self.options.size, self.options.size,
                               Texture.TFloat, Texture.FRgba16)
            tex.setMinfilter(Texture.FTNearest)
            tex.setMagfilter(Texture.FTNearest)
            tex.setWrapU(Texture.WMClamp)
            tex.setWrapV(Texture.WMClamp)
            self.heightTextures.append(tex)

        # Also create the shader which updates the spectrum
        self.shaderUpdate = BetterShader.loadCompute(
            "Water/Update.compute")
        self.nodeUpdate = NodePath("update")
        self.nodeUpdate.setShader(self.shaderUpdate)
        self.nodeUpdate.setShaderInput("outH0x", self.heightTextures[0])
        self.nodeUpdate.setShaderInput("outH0y", self.heightTextures[1])
        self.nodeUpdate.setShaderInput("outH0z", self.heightTextures[2])
        self.nodeUpdate.setShaderInput("initialHeight", self.texInitialHeight)
        self.nodeUpdate.setShaderInput("N", LVecBase2i(self.options.size))
        self.nodeUpdate.setShaderInput("time", self.ptaTime)
        self.attrUpdate = self.nodeUpdate.getAttrib(ShaderAttrib)

        # Create 3 FFTs
        self.fftX = GPUFFT(self.options.size, self.heightTextures[0],
                           self.options.normalizationFactor)
        self.fftY = GPUFFT(self.options.size, self.heightTextures[1],
                           self.options.normalizationFactor)
        self.fftZ = GPUFFT(self.options.size, self.heightTextures[2],
                           self.options.normalizationFactor)

        self.combineNode = NodePath("Combine")
        self.combineNode.setShader(self.combineShader)
        self.combineNode.setShaderInput(
            "displacementX", self.fftX.getResultTexture())
        self.combineNode.setShaderInput(
            "displacementY", self.fftY.getResultTexture())
        self.combineNode.setShaderInput(
            "displacementZ", self.fftZ.getResultTexture())
        self.combineNode.setShaderInput("normalDest", self.normalTex)
        self.combineNode.setShaderInput(
            "displacementDest", self.displacementTex)
        self.combineNode.setShaderInput(
            "N", LVecBase2i(self.options.size))
        self.combineNode.setShaderInput(
            "choppyScale", self.options.choppyScale)
        self.combineNode.setShaderInput(
            "gridLength", self.options.patchLength)
        # Store only the shader attrib as this is way faster
        self.attrCombine = self.combineNode.getAttrib(ShaderAttrib)

    def _getGaussianRandom(self):
        """ Returns a gaussian random number """
        u1 = generateRandom()
        u2 = generateRandom()
        if u1 < 1e-6:
            u1 = 1e-6
        return sqrt(-2 * log(u1)) * cos(2 * pi * u2)

    def setup(self):
        """ Setups the manager """

        Globals.base.graphicsEngine.dispatch_compute(
            (self.options.size / 16,
             self.options.size / 16, 1), self.attrInitialHeight,
            Globals.base.win.get_gsg())

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

        self.ptaTime[0] = 1 + \
            Globals.clock.getFrameTime() * self.options.timeScale

        Globals.base.graphicsEngine.dispatch_compute(
            (self.options.size / 16,
             self.options.size / 16, 1), self.attrUpdate,
            Globals.base.win.get_gsg())

        self.fftX.execute()
        self.fftY.execute()
        self.fftZ.execute()

        # Execute the shader which combines the 3 displacement maps into
        # 1 displacement texture and 1 normal texture. We could use dFdx in
        # the fragment shader, however that gives no accurate results as
        # dFdx returns the same value for a 2x2 pixel block
        Globals.base.graphicsEngine.dispatch_compute(
            (self.options.size / 16,
             self.options.size / 16, 1), self.attrCombine,
            Globals.base.win.get_gsg())
