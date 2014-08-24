from Code.DebugObject import DebugObject
from Code.BetterShader import BetterShader
from Code.Globals import Globals
from GPUFFT import GPUFFT

from panda3d.core import Texture, NodePath, ShaderAttrib, Vec2, LVecBase2i
from panda3d.core import PTAFloat, PNMImage, LVecBase3d

from random import random as generateRandom
from random import seed as setRandomSeed
import math


class OceanOptions:

    """ This class stores all options required for the WaterDisplacement """
    size = 128
    wind = Vec2(74, 64)
    length = 8192.0
    a = 0.00005
    gravity = 9.81
    timeShift = 10
    normalizationFactor = 20000


class WaterDisplacement(DebugObject):

    """ This is a wrapper arroudn the GPU-FFT, which handles generating a
    phillips spectrum, updating it, and performing an inverse  fft over it.
    The result is a displacement map (with one channel only).

    If you want to have multiple displacement maps (e.g. x, y, z), then you
    should use multiple instances of this class. To get independent heightmaps,
    you should also set a different seed for all classes.

    The resulting heightfield can be retrieved with getDisplacementTexture().
    """

    def __init__(self, options=None, seed=123):
        """ Creates a new displacement map generator, with given OceanOptions.
        The seed should be a number from 0 .. 100, and will randomize the
        output. Call setup once after you created this instance, and update
        every frame """

        DebugObject.__init__(self, "WaterDisplacement")
        self.debug("Creating FFT Handle")

        if options is None:
            options = OceanOptions()

        # Check power of 2, also 512 does not work right now
        # (There is some issue with the gaussian random numbers)
        if options.size & (options.size - 1) != 0 or options.size < 16:
            self.error("Invalid fft size:", options.size)
            return

        self.options = options

        # Create the texture wwhere the intial height (HTilde0) is stored.
        self.texInitialHeight = Texture("InitialHeight")
        self.texInitialHeight.setup2dTexture(
            options.size, options.size, Texture.TFloat, Texture.FRgba16)
        self.texCurrentHeight = Texture("CurrentHeight")
        self.texCurrentHeight.setup2dTexture(
            options.size, options.size, Texture.TFloat, Texture.FRgba16)

        # Create a gaussian random texture, as shaders aren't well suited
        # for that
        setRandomSeed(seed)
        self.randomStorage = PNMImage(128, 128, 4)
        self.randomStorage.setMaxval((2 ** 16) - 1)

        for x in xrange(128):
            for y in xrange(128):
                rand1 = self._getGaussianRandom() / 10.0 + 0.5
                rand2 = self._getGaussianRandom() / 10.0 + 0.5
                self.randomStorage.setXel(x, y, LVecBase3d(rand1.x,
                                                           rand1.y, rand2.x))
                self.randomStorage.setAlpha(x, y, rand2.y)

        self.randomStorageTex = Texture("RandomStorage")
        self.randomStorageTex.load(self.randomStorage)
        self.randomStorageTex.setFormat(Texture.FRgba16)

        # Create the shader which populates the initial height texture
        self.shaderInitialHeight = BetterShader.loadCompute(
            "Shader/Water/InitialHeight.compute")
        self.nodeInitialHeight = NodePath("initialHeight")
        self.nodeInitialHeight.setShader(self.shaderInitialHeight)
        self.nodeInitialHeight.setShaderInput("dest", self.texInitialHeight)
        self.nodeInitialHeight.setShaderInput("N", LVecBase2i(options.size))
        self.nodeInitialHeight.setShaderInput("A", options.a)
        self.nodeInitialHeight.setShaderInput("oceanLength", options.length)
        self.nodeInitialHeight.setShaderInput("gravity", options.gravity)
        self.nodeInitialHeight.setShaderInput("wind", options.wind)
        self.nodeInitialHeight.setShaderInput(
            "randomTex", self.randomStorageTex)

        # Also create the shader which updates the spectrum
        self.shaderUpdate = BetterShader.loadCompute(
            "Shader/Water/Update.compute")
        self.nodeUpdate = NodePath("update")
        self.nodeUpdate.setShader(self.shaderUpdate)
        self.nodeUpdate.setShaderInput("dest", self.texCurrentHeight)
        self.nodeUpdate.setShaderInput("initialHeight", self.texInitialHeight)
        self.nodeUpdate.setShaderInput("time", 0.1)
        self.nodeUpdate.setShaderInput("N", LVecBase2i(options.size))
        self.nodeUpdate.setShaderInput("length", options.length)
        self.nodeUpdate.setShaderInput("gravity", options.gravity)

        # Create a PTA Float for the time, so we don't have to modify the
        # shader attrib every frame, and also store the shader attrib
        self.ptaTime = PTAFloat.emptyArray(1)
        self.nodeUpdate.setShaderInput("time", self.ptaTime)
        self.sattrUpdate = self.nodeUpdate.getAttrib(ShaderAttrib)

        # Now create the fft handler, which will execute an inverse 2d fft
        self.fft = GPUFFT(options.size, self.texCurrentHeight,
                          self.options.normalizationFactor)

    def _getGaussianRandom(self):
        w = 10.0
        iterations = 10
        while w >= 1.0 and iterations > 0:
            iterations -= 1
            x1 = 2.0 * generateRandom() - 1.0
            x2 = 2.0 * generateRandom() - 1.0
            w = x1 * x1 + x2 * x2
        w = math.sqrt((-2.0 * math.log(w)) / w)
        return Vec2(x1 * w, x2 * w)

    def setup(self):
        """ Initis this instance, required to use this """
        self._executeShader(self.nodeInitialHeight)
        self.update()

    def update(self, t=None):
        """ Updates the instance, adjusting the heightfield to match the given
        time <t>. If <t> is None, the current time will be used. """
        if t is None:
            t = Globals.clock.getFrameTime() * self.options.timeShift
        self.ptaTime[0] = t
        self._executeShaderAttrib(self.sattrUpdate)
        self.fft.execute()

    def getDisplacementTexture(self):
        """ Returns the 2D displacement texture, which gets generated by
        calling update() """
        return self.fft.getResultTexture()

    def _executeShader(self, node):
        """ Internal method to execute a shader, fetching the inputs from a
        NodePath """
        sattr = node.get_attrib(ShaderAttrib)
        self._executeShaderAttrib(sattr)

    def _executeShaderAttrib(self, sattr):
        """ Internal method to execute a shader, reusing a ShaderAttrib """
        Globals.base.graphicsEngine.dispatch_compute(
            (self.options.size / 16, self.options.size / 16, 1), sattr,
            Globals.base.win.get_gsg())
