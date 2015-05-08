

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
            7:  4 * 1, # RGBA (Unkown type, we will just assume 8 bit)
            16: 4 * 1, # RGBA8
            21: 4 * 2, # RGBA16
            22: 4 * 4, # RGBA32
            25: 3,     # Depth 24 Bit
            26: 4,     # Depth 32 Bit
            27: 2,     # FR16     
            34: 4,     # FR32i
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

        # Mipmaps take approx 33% of the texture size, so just multiply the pixel
        # count by that amount
        if tex.usesMipmaps():
            pixelCount *= 1.33

        # Multiply the size of the component by the amount of pixels
        dataSize = componentSize * pixelCount
        return dataSize

    @classmethod
    def addTexture(self, name, tex):
        """ Adds a texture to the list of textures which are currently used """
        self.memoryEntries["[TEX] " + name] = self._calculateTexSize(tex)

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
            self.memoryEntries[name + "." + targetType] = texSize

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
        for key, val in sorted(self.memoryEntries.iteritems(), key = lambda v: -v[1]):
            valMB = round(val / (1024.0 * 1024.0), 1)
            outputLine = ""
            outputLine += key.ljust(50, ' ')
            outputLine += str(valMB) + " MB"
            total += val

            print outputLine

        print "-"*79
        print " "*49, round(total / (1024.0 * 1024.0), 1), "MB"