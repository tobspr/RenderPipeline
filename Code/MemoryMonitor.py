

from RenderTargetType import RenderTargetType


class MemoryMonitor:


    memoryEntries = {}

    @classmethod
    def _calculateTexSize(self, tex):
        """ This internal function computes the approximate size of a texture
        in byte on the gpu. """

        # Assigns a texture format a size
        textureTypes = {
            16: 4 * 1, # RGBA8
            21: 4 * 2, # RGBA16
            22: 4 * 4, # RGBA32
            26: 4,     # Depth 32 Bit
            27: 2,     # FR16     
            34: 4,     # FR32i
        }

        form = tex.getFormat()
        componentSize = 0

        if form in textureTypes:
            componentSize = textureTypes[form]
        else:
            print "MemoryMonitor: Unkown component type:", form, tex.getName()

        pixelCount = tex.getXSize() * tex.getYSize() * tex.getZSize()

        dataSize = componentSize * pixelCount
        return dataSize

    @classmethod
    def addTexture(self, name, tex):
        """ Adds a texture to the list of textures which are currently used """
        # Compute texture size
        dataSize = self._calculateTexSize(tex)
        self.memoryEntries["[TEX] " + name] = dataSize

    @classmethod
    def addRenderTarget(self, name, target):
        """ Adds a render target to the list of targets which are currently used """
        # Iterate over all targets
        for targetType in RenderTargetType.All:
            if not target.hasTarget(targetType):
                continue

            # Extract textures
            tex = target.getTarget(targetType)
            texSize = self._calculateTexSize(tex)
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
        """ Analyzes the used memory """
        print "VRAM Usage:"
        for key, val in sorted(self.memoryEntries.items(), key = lambda v: -v[1]):
            valMB = round(val / (1024.0 * 1024.0), 1)
            outputLine = ""
            outputLine += key.ljust(50, ' ')
            outputLine += str(valMB) + " MB"

            print outputLine
