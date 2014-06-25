

from panda3d.core import Shader
from os.path import isfile, join


# Small wrapper arround panda3d.core.Shader which supports
# includes in glsl shaders
class BetterShader:

    # Include stack, which mentions the already included
    # files. This prevents recursive inclusion. Stack
    # gets cleared after creating a shader.
    _GlobalIncludeStack = []

    # Root directory where all the shaders are stored
    # This is usefull so you don't have to change all your 
    # Shaders when you move them to a new location.
    # Also include directives are shorter then. Set to ""
    # to disable this feature
    _GlobalShaderPath = "Shader/"

    # Loads a compute shader
    @classmethod
    def loadCompute(self, source):
        result = Shader.makeCompute(Shader.SLGLSL, self._handleIncludes(source))
        self._clearIncludeStack()
        return result

    # Loads a normal shader
    # Order is vertex, fragment, geometry, tesseval, tesscontrol
    @classmethod
    def load(self, *args):
        newArgs = []
        for arg in args:
            newArgs.append(self._handleIncludes(arg))
        result = Shader.make(Shader.SLGLSL, *newArgs)
        self._clearIncludeStack()
        return result

    # Internal method to clear the include stack
    @classmethod
    def _clearIncludeStack(self):
        self._GlobalIncludeStack = []

    # Internal (recursive) method to parse #include's
    @classmethod
    def _handleIncludes(self, source):

        with open(source, "r") as handle:
            content = handle.readlines()

        newContent = ""
        includeIdentifier = "#include "

        # Iterate through lines
        for line_idx, line in enumerate(content):
            lineStrip = line.strip()
            if lineStrip.startswith(includeIdentifier):
                includePart = lineStrip[len(includeIdentifier):].strip()

                # Filename is surrounded by braces
                # Todo: maybe also support ->'<- additionally to ->"<-
                if includePart.startswith('"') and includePart.endswith('"'):

                    # Extract include part
                    properIncludePart = join(self._GlobalShaderPath, includePart[1:-1])

                    # And check if file exists
                    if isfile(properIncludePart):
                        
                        # Check for recursive includes
                        if properIncludePart in self._GlobalIncludeStack:
                            print "BetterShader: Ignoring recursive include:",properIncludePart
                        else:
                            self._GlobalIncludeStack.append(properIncludePart)
                            newContent += self._handleIncludes(properIncludePart)
                            newContent += "#line " + str(line_idx)
                    else:
                        print "BetterShader: Failed to load '" + str(properIncludePart) + "'!"
                else:
                    print "BetterShader: Invalid include:",includePart

                continue

            newContent += lineStrip + "\n"

        return newContent
