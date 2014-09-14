
from panda3d.core import PNMImage, Texture, LVecBase3d, NodePath
from panda3d.core import ShaderAttrib, LVecBase2i, Vec2

from Code.DebugObject import DebugObject
from Code.BetterShader import BetterShader
from Code.Globals import Globals

import math


class GPUFFT(DebugObject):

    """ This is a collection of compute shaders to generate the inverse
    fft efficiently on the gpu, with butterfly FFT and precomputed weights """

    def __init__(self, N, sourceTex, normalizationFactor):
        """ Creates a new fft instance. The source texture has to specified
        from the begining, as the shaderAttributes are pregenerated for
        performance reasons """
        DebugObject.__init__(self, "GPU-FFT")

        self.size = N
        self.log2Size = int(math.log(N, 2))
        self.normalizationFactor = normalizationFactor

        # Create a ping and a pong texture, because we can't write to the
        # same texture while reading to it (that would lead to unexpected
        # behaviour, we could solve that by using an appropriate thread size,
        # but it works fine so far)
        self.pingTexture = Texture("FFTPing")
        self.pingTexture.setup2dTexture(
            self.size, self.size, Texture.TFloat, Texture.FRgba32)
        self.pongTexture = Texture("FFTPong")
        self.pongTexture.setup2dTexture(
            self.size, self.size, Texture.TFloat, Texture.FRgba32)
        self.sourceTex = sourceTex

        for tex in [self.pingTexture, self.pongTexture, sourceTex]:
            tex.setMinfilter(Texture.FTNearest)
            tex.setMagfilter(Texture.FTNearest)
            tex.setWrapU(Texture.WMClamp)
            tex.setWrapV(Texture.WMClamp)

        # Pregenerate weights & indices for the shaders
        self._computeWeighting()

        # Pre generate the shaders, we have 2 passes: Horizontal and Vertical
        # which both execute log2(N) times with varying radii
        self.horizontalFFTShader = BetterShader.loadCompute(
            "Shader/Water/HorizontalFFT.compute")
        self.horizontalFFT = NodePath("HorizontalFFT")
        self.horizontalFFT.setShader(self.horizontalFFTShader)
        self.horizontalFFT.setShaderInput(
            "precomputedWeights", self.weightsLookupTex)
        self.horizontalFFT.setShaderInput("N", LVecBase2i(self.size))

        self.verticalFFTShader = BetterShader.loadCompute(
            "Shader/Water/VerticalFFT.compute")
        self.verticalFFT = NodePath("VerticalFFT")
        self.verticalFFT.setShader(self.verticalFFTShader)
        self.verticalFFT.setShaderInput(
            "precomputedWeights", self.weightsLookupTex)
        self.verticalFFT.setShaderInput("N", LVecBase2i(self.size))

        # Create a texture where the result is stored
        self.resultTexture = Texture("Result")
        self.resultTexture.setup2dTexture(
            self.size, self.size, Texture.TFloat, Texture.FRgba16)
        self.resultTexture.setMinfilter(Texture.FTLinear)
        self.resultTexture.setMagfilter(Texture.FTLinear)

        # Prepare the shader attributes, so we don't have to regenerate them
        # every frame -> That is VERY slow (3ms per fft instance)
        self._prepareAttributes()

    def getResultTexture(self):
        """ Returns the result texture, only contains valid data after execute
        was called at least once """
        return self.resultTexture

    def _generateIndices(self, storageA, storageB):
        """ This method generates the precompute indices, see
        http://cnx.org/content/m12012/latest/image1.png """
        numIter = self.size
        offset = 1
        step = 0
        for i in xrange(self.log2Size):
            numIter = numIter >> 1
            step = offset
            for j in xrange(self.size):
                goLeft = (j / step) % 2 == 1
                indexA, indexB = 0, 0
                if goLeft:
                    indexA, indexB = j - step, j
                else:
                    indexA, indexB = j, j + step

                storageA[i][j] = indexA
                storageB[i][j] = indexB
            offset = offset << 1

    def _generateWeights(self, storage):
        """ This method generates the precomputed weights """

        # Using a custom pi variable should force the calculations to use
        # high precision (I hope so)
        pi = 3.141592653589793238462643383
        numIter = self.size / 2
        numK = 1
        resolutionFloat = float(self.size)
        for i in xrange(self.log2Size):
            start = 0
            end = 2 * numK
            for b in xrange(numIter):
                K = 0
                for k in xrange(start, end, 2):
                    fK = float(K)
                    fNumIter = float(numIter)
                    weightA = Vec2(
                        math.cos(2.0 * pi * fK * fNumIter / resolutionFloat),
                        -math.sin(2.0 * pi * fK * fNumIter / resolutionFloat))
                    weightB = Vec2(
                        -math.cos(2.0 * pi * fK * fNumIter / resolutionFloat),
                        math.sin(2.0 * pi * fK * fNumIter / resolutionFloat))
                    storage[i][k / 2] = weightA
                    storage[i][k / 2 + numK] = weightB
                    K += 1
                start += 4 * numK
                end = start + 2 * numK
            numIter = numIter >> 1
            numK = numK << 1

    def _reverseRow(self, indices):
        """ Reverses the bits in the given row. This is required for inverse
        fft (actually we perform a normal fft, but reversing the bits gives
        us an inverse fft) """
        mask = 0x1
        for j in xrange(self.size):
            val = 0x0
            temp = int(indices[j])  # Int is required, for making a copy
            for i in xrange(self.log2Size):
                t = mask & temp
                val = (val << 1) | t
                temp = temp >> 1
            indices[j] = val

    def _computeWeighting(self):
        """ Precomputes the weights & indices, and stores them in a texture """
        indicesA = [[0 for i in xrange(self.size)]
                    for k in xrange(self.log2Size)]
        indicesB = [[0 for i in xrange(self.size)]
                    for k in xrange(self.log2Size)]
        weights = [[Vec2(0.0) for i in xrange(self.size)]
                   for k in xrange(self.log2Size)]

        self.debug("Pre-Generating indices ..")
        self._generateIndices(indicesA, indicesB)
        self._reverseRow(indicesA[0])
        self._reverseRow(indicesB[0])

        self.debug("Pre-Generating weights ..")
        self._generateWeights(weights)

        # Create storage for the weights & indices
        self.weightsLookup = PNMImage(self.size, self.log2Size, 4)
        self.weightsLookup.setMaxval((2 ** 16) - 1)
        self.weightsLookup.fill(0.0)

        # Populate storage
        for x in xrange(self.size):
            for y in xrange(self.log2Size):
                indexA = indicesA[y][x]
                indexB = indicesB[y][x]
                weight = weights[y][x]

                self.weightsLookup.setRed(x, y, indexA / float(self.size))
                self.weightsLookup.setGreen(x, y, indexB / float(self.size))
                self.weightsLookup.setBlue(x, y, weight.x * 0.5 + 0.5)
                self.weightsLookup.setAlpha(x, y, weight.y * 0.5 + 0.5)

        # Convert storage to texture so we can use it in a shader
        self.weightsLookupTex = Texture("Weights Lookup")
        self.weightsLookupTex.load(self.weightsLookup)
        self.weightsLookupTex.setFormat(Texture.FRgba16)
        self.weightsLookupTex.setMinfilter(Texture.FTNearest)
        self.weightsLookupTex.setMagfilter(Texture.FTNearest)
        self.weightsLookupTex.setWrapU(Texture.WMClamp)
        self.weightsLookupTex.setWrapV(Texture.WMClamp)

    def _prepareAttributes(self):
        """ Prepares all shaderAttributes, so that we have a list of
        ShaderAttributes we can simply walk through in the update method,
        that is MUCH faster than using setShaderInput, as each call to
        setShaderInput forces the generation of a new ShaderAttrib """
        self.attributes = []
        textures = [self.pingTexture, self.pongTexture]

        currentIndex = 0
        firstPass = True

        # Horizontal
        for step in xrange(self.log2Size):
            source = textures[currentIndex]
            dest = textures[1 - currentIndex]

            if firstPass:
                source = self.sourceTex
                firstPass = False

            index = self.log2Size - step - 1
            self.horizontalFFT.setShaderInput("source", source)
            self.horizontalFFT.setShaderInput("dest", dest)
            self.horizontalFFT.setShaderInput(
                "butterflyIndex", LVecBase2i(index))
            self._queueShader(self.horizontalFFT)
            currentIndex = 1 - currentIndex

        # Vertical
        for step in xrange(self.log2Size):
            source = textures[currentIndex]
            dest = textures[1 - currentIndex]
            isLastPass = step == self.log2Size - 1
            if isLastPass:
                dest = self.resultTexture
            index = self.log2Size - step - 1
            self.verticalFFT.setShaderInput("source", source)
            self.verticalFFT.setShaderInput("dest", dest)
            self.verticalFFT.setShaderInput(
                "isLastPass", isLastPass)
            self.verticalFFT.setShaderInput(
                "normalizationFactor", self.normalizationFactor)
            self.verticalFFT.setShaderInput(
                "butterflyIndex", LVecBase2i(index))
            self._queueShader(self.verticalFFT)

            currentIndex = 1 - currentIndex

    def execute(self):
        """ Executes the inverse fft once """
        for attr in self.attributes:
            self._executeShader(attr)

    def _queueShader(self, node):
        """ Internal method to fetch the ShaderAttrib of a node and store it
        in the update queue """
        sattr = node.getAttrib(ShaderAttrib)
        self.attributes.append(sattr)

    def _executeShader(self, sattr):
        """ Internal method to execute a shader by a given ShaderAttrib """
        Globals.base.graphicsEngine.dispatch_compute(
            (self.size / 16, self.size / 16, 1), sattr,
            Globals.base.win.get_gsg())
