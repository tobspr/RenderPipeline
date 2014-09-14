from direct.stdpy.file import open, isdir, isfile, join, listdir
from panda3d.core import Shader, Filename
from Globals import Globals


class BetterShader:

    """ Small wrapper arround panda3d.core.Shader which supports
    includes in glsl shaders via #include "filename", and also caches
    shaders """

    # Include stack, which mentions the already included
    # files. This prevents recursive inclusion. Stack
    # gets cleared after creating a shader.
    _GlobalIncludeStack = []

    # Root directory where all the shaders are stored
    # This is useful so you don't have to change all your
    # Shaders when you move them to a new location.
    # Also include directives are shorter then. Set to ""
    # to disable this feature
    _GlobalShaderPath = "Shader"

    # Wheter to dump the generated shaders to disk. This is very
    # handy and should only be disabled in production
    _DumpShaders = False

    _ShaderCache = {}
    _ShaderIDs = {}
    _NextID = 1000

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

        newArgs = []
        toHash = ""

        for arg in args:
            if len(arg) < 1:
                newArgs.append("")
                continue
            content = self._handleIncludes(arg)
            newArgs.append(content)
            toHash += content
            self._writeDebugShader("Shader-" + str(arg), content)
            self._clearIncludeStack()

        # Check if we already have the result cached
        hashed = hash(toHash)
        if hashed in self._ShaderCache:
            # Cache entry found
            return self._ShaderCache[hashed]

        shaderName = args[1].replace("Shader", "").split(".")[0].lstrip("/")

        result = Shader.make(Shader.SLGLSL, *newArgs)
        self._ShaderCache[hashed] = result
        return result

    @classmethod
    def _clearIncludeStack(self):
        """ Internal method to clear the include stack """
        self._GlobalIncludeStack = []

    @classmethod
    def _writeDebugShader(self, name, content):
        """ Internal method to dump shader for debugging """

        if not self._DumpShaders:
            return

        cachePath = "PipelineTemp"
        if not isdir(cachePath):
            print "Cache path does not exist!:", cachePath
            print "Disabling shader dump"
            self._DumpShaders = False
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

        ID = self._ShaderIDs.get(source, None)
        if ID is None:
            ID = self._NextID
            self._ShaderIDs[source] = ID
            print ID, source
            self._NextID += 1

        newContent += "#line 1 %d\n" % (ID)

        # Iterate through lines
        for line_idx, line in enumerate(content):
            lineStrip = line.strip()
            if lineStrip.startswith(includeIdentifier):
                includePart = lineStrip[len(includeIdentifier):].strip()

                # Filename is surrounded by braces
                # Todo: maybe also support ->'<- additionally to ->"<-
                if includePart.startswith('"') and includePart.endswith('"'):

                    # Special case
                    if includePart == '"%ShaderAutoConfig%"':
                        properIncludePart = "PipelineTemp/ShaderAutoConfig.include"
                    else:
                        # Extract include part
                        properIncludePart = Filename.fromOsSpecific(join(
                            self._GlobalShaderPath, includePart[1:-1])).toOsGeneric()

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

                            newContent += "#line %d %d\n" % (line_idx + 2, ID)

                    else:
                        print "BetterShader: Failed to load '" + str(properIncludePart) + "'!"
                else:
                    print "BetterShader: Invalid include:", includePart

                continue

            newContent += line.rstrip() + "\n"

        return newContent
