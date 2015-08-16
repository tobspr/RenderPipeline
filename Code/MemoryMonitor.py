
from panda3d.core import Texture

from RenderTargetType import RenderTargetType


class MemoryMonitor:

    """ The memory monitor keeps track of all gpu ressources. All render targets
    and textures should be registered to the monitor. The used memory can be
    seen by calling analyzeMemory. """


    # Internal storage for all entries
    memoryEntries = {}

    @classmethod
    def _calculateTexSize(self, tex):
        """ This internal function computes the approximate size of a texture
        in byte on the gpu. """

        # Assign the texture format a size
        textureTypes = {
            3:  1,     # FRED
            6:  1,     # ALPHA
            7:  4,     # RGB (Unkown type, we will just assume 8 bit)
            9:  4,     # FRGBA8
            12: 4,     # RGBA (Unkown type, we will just assume 8 bit)
            18: 1,     # LUMINANCE
            19: 2,     # LUMINANCE_ALPHA
            16: 4,     # RGBA8
            21: 8,     # RGBA16
            22: 16,    # RGBA32
            24: 2,     # FDEPTHCOMOPONENT
            25: 4,     # Depth 24 Bit
            26: 4,     # Depth 32 Bit
            27: 2,     # FR16 
            29: 8,     # FRGB16
            30: 4,     # FSRGB
            31: 4,     # FSRGB_ALPHA    
            34: 4,     # FR32i
            35: 4,     # FR32,
            42: 4,     # FR11G11B10
        }


        # Get format and compute size per component
        form = tex.getFormat()
        componentSize = 0

        if form in textureTypes:
            componentSize = textureTypes[form]
        else:
            print "MemoryMonitor: Unkown type:", form, tex.getName()

        # Fetch the amount of pixels
        pixelCount = tex.getXSize() * tex.getYSize() * tex.getZSize()

        # Check for deprecated formats
        deprecated = [18, 19, 6]

        if form in deprecated:
            # print "DEPRECATED FORMAT:", form, "USED BY",tex.getName()
            pass

        # Multiply the size of the component by the amount of pixels
        dataSize = int(componentSize * pixelCount)
        
        # Mipmaps take approx 33% of the texture size, so just multiply it with that amount
        if tex.usesMipmaps():
            dataSize = (dataSize * 4) / 3

        # if dataSize != tex.estimateTextureMemory():
            # print "Format",form,"does not match:", dataSize, "vs", tex.estimateTextureMemory()

        return dataSize

    @classmethod
    def addTexture(self, name, tex):
        """ Adds a texture to the list of textures which are currently used """
        self.memoryEntries["[TEX] " + name] = (self._calculateTexSize(tex), tex)

    @classmethod
    def addRenderTarget(self, name, target):
        """ Adds a render target to the list of targets which are currently used """

        # Iterate over all attachments
        for targetType in RenderTargetType.All:
            if not target.hasTarget(targetType):
                continue

            # Extract attachment textures and calculate their size
            tex = target.getTarget(targetType)
            texSize = self._calculateTexSize(tex)

            # Store the texture
            self.memoryEntries[name + "." + targetType] = (texSize, tex)

    @classmethod
    def unregisterRenderTarget(self, name, target):
        """ Removes a render target from the list of targets which are currently used """
        for targetType in RenderTargetType.All:
            if not target.hasTarget(targetType):
                continue
            targetName = name + "." + targetType
            del self.memoryEntries[targetName]

    @classmethod
    def analyzeMemory(self):
        """ Analyzes the used memory, printing out the statistics on the console """
        print "VRAM Usage:"

        total = 0.0

        for key, (val, handle) in sorted(self.memoryEntries.iteritems(), key = lambda v: -v[1][0]):
            valMB = round(val / (1024.0 * 1024.0), 1)
            outputLine = ""
            outputLine += key.ljust(50, ' ')
            outputLine += str(valMB) + " MB"
            total += val

            print outputLine

        print "-"*79
        print " "*49, round(total / (1024.0 * 1024.0), 1), "MB"

    @classmethod
    def getEstimatedMemUsage(self):
        """ Returns the estimated memory usage in Bytes """
        totalSum = 0
        for key, (val, handle) in self.memoryEntries.iteritems():
            totalSum += val
        return totalSum

    @classmethod
    def isRegistered(self, tex):
        """ Checks if the texture is registered """
        for key, (val, handle) in self.memoryEntries.iteritems():
            if handle == tex:
                return True
        return False