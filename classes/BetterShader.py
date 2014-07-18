
from panda3d.core import Shader
from os.path import isfile, join, isdir
from os import makedirs


class BetterShader:

    """ Small wrapper arround panda3d.core.Shader which supports
    includes in glsl shaders via #include "filename" """

    # Include stack, which mentions the already included
    # files. This prevents recursive inclusion. Stack
    # gets cleared after creating a shader.
    _GlobalIncludeStack = []

    # Root directory where all the shaders are stored
    # This is useful so you don't have to change all your
    # Shaders when you move them to a new location.
    # Also include directives are shorter then. Set to ""
    # to disable this feature
    _GlobalShaderPath = "Shader/"

    @classmethod
    def loadCompute(self, source):
        """ Loads a compute shader """

        content = self._handleIncludes(source)
        result = Shader.makeCompute(Shader.SLGLSL, content)
        self._writeDebugShader("Compute-" + str(source), content)
        self._clearIncludeStack()
        return result

    @classmethod
    def load(self, *args):
        """ Loads a shader in the order: vertex, fragment,
        geometry, tesseval, tesscontrol """

        print "Loading shader from",args[-1].replace("Shader/", "")

        newArgs = []

        for arg in args:
            if len(arg) < 1:
                print "append '' for geometry shader!"
                newArgs.append("")
                continue
            content = self._handleIncludes(arg)
            newArgs.append(content)
            # print "append content for shader"
            self._writeDebugShader("Shader-" + str(arg), content)
            self._clearIncludeStack()


        result = Shader.make(Shader.SLGLSL, *newArgs)
        return result

    @classmethod
    def _clearIncludeStack(self):
        """ Internal method to clear the include stack """
        self._GlobalIncludeStack = []

    @classmethod
    def _writeDebugShader(self, name, content):
        """ Internal method to dump shader for debugging """
        cachePath = join(self._GlobalShaderPath, "Cache")
        if not isdir(cachePath):
            try:
                makedirs(cachePath)
            except Exception, msg:
                print "Could not create", cachePath, ":", msg
                return

        writeName = name.strip().replace("/", "-").replace(".", "_") + ".bin"
        with open(join(cachePath, writeName), "w") as handle:
            handle.write(str(content))

    @classmethod
    def _handleIncludes(self, source):
        """ Internal (recursive) method to parse #include's """

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
                    properIncludePart = join(
                        self._GlobalShaderPath, includePart[1:-1])

                    # And check if file exists
                    if isfile(properIncludePart):

                        # Check for recursive includes
                        if properIncludePart in self._GlobalIncludeStack:
                            # print "BetterShader: Ignoring recursive
                            # include:",properIncludePart
                            pass

                        else:
                            self._GlobalIncludeStack.append(properIncludePart)
                            newContent += "\n// FILE: '" + \
                                str(properIncludePart) + "' \n"
                            newContent += self._handleIncludes(
                                properIncludePart).strip() + "\n"
                    else:
                        print "BetterShader: Failed to load '" + str(properIncludePart) + "'!"
                else:
                    print "BetterShader: Invalid include:", includePart

                continue

            newContent += line.rstrip() + "\n"

        return newContent
