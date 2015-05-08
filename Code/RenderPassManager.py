import time

from DebugObject import DebugObject

from direct.stdpy.file import open

class RenderPassManager(DebugObject):

    """ This class processes a list of RenderPasses and matches them in an order
    that they can be executed sequentially. It also handles user defined variables """

    def __init__(self):
        """ Creates a new render pass manager. There should only be 1 instance
        at a time """
        DebugObject.__init__(self, "RenderPassManager")
        self.renderPasses = {}
        self.staticVariables = {}
        self.dynamicVariables = {}
        self.defines = {}

    def registerPass(self, renderPass):
        """ Register a new RenderPass """
        self.renderPasses[renderPass.getID()] = renderPass

    def registerStaticVariable(self, name, value):
        """ Registers a new static variable. Static variables are bound by value,
        that means you have to know the value when binding it (except when using a PTA) """
        self.staticVariables[name] = value

    def registerDynamicVariable(self, name, handler):
        """ Registers a new dynamic variable. Dynamic variables are bound when the
        render target is created. The handler should be a function which takes a
        RenderPass as the first parameter and applies the inputs to that pass. It
        is very well possible that the handler binds multiple inputs, e.g. a whole
        structure """ 
        self.dynamicVariables[name] = handler

    def registerDefine(self, name, value):
        """ Registers a define which will be written to the shader auto config """
        self.defines[name] = value

    def unregisterDefine(self, name):
        """ Unregisters a define which was set by register define """
        if name in self.defines:
            del self.defines[name]

    def updateStaticVariable(self, name, value):
        """ Iterates over all passes, updating the shader input for that variable """
        raise NotImplementedError()

    def updateDynamicVariable(self, name, handler=None):
        """ Iterates over all passes, calling the handler of that variable. If
        no new handler is specified, the old hander will be taken, otherwise the
        handler will get replaced """
        raise NotImplementedError()


    def _havePass(self, name):
        """ Internal method to check if a render pass exists """
        return name in self.renderPasses

    def _canAttach(self, renderPass):
        """ Internal method to check if all required inputs are set for a pass
        during the sorting algorithm """

        # Iterate over all inputs of the pass
        inputs = renderPass.getRequiredInputs()
        for inputID, inputSource in inputs.items():
            firstInput = self._getFirstAvailableInput(inputSource, checkVariables = False)
            if not firstInput:
                # self.debug("HINT:Missing",inputSource, "for", renderPass.getID())
                return False

        return True

    def _makeUniformsAvailable(self, renderPass):
        """ Internal method to register all outputs of a RenderPass to the list
        of already inserted outputs during sorting algorithm """
        outputs = renderPass.getOutputs().keys()
        for outputID in outputs:
            self._availableUniformNames.append(outputID)

    def _checkVariableAvailable(self, variableName):
        """ Internal method to check if a variable was specified by the user """
        variableName = variableName.split(".")[1]
        if variableName in self.staticVariables or variableName in self.dynamicVariables:
            return True
        return False

    def _getFirstAvailableInput(self, inputList, checkVariables=True):
        """ Internal method to choose the first available uniform from a list of
        uniforms """
        if type(inputList) == list:

            waitForPass = False

            for entry in inputList:
                passName = entry.split(".")[0]

                if entry in self._availableUniformNames:
                    if waitForPass and not checkVariables:
                        return False
                    return entry

                if self._havePass(passName):
                    waitForPass = True
                
                if passName == "Variables" and self._checkVariableAvailable(entry):
                    if waitForPass and not checkVariables:
                        return False 

                    return entry                    

            # self.error("No input of",inputList,"is available")
            return False

        if inputList in self._availableUniformNames:
            return inputList

        if inputList.startswith("Variables.") and  self._checkVariableAvailable(inputList):
            return inputList

        return False

    def anyPassRequires(self, uniformName):
        """ Checks if any of the currently attached passes requires an uniform
        with that name """

        for renderPass in self.renderPasses.values():
            inputs = renderPass.getRequiredInputs()
            if uniformName in inputs.values():
                self.debug(renderPass,"requires value",uniformName)
                return True

        return False

    def anyPassProduces(self, uniformName):
        """ Checks if any of the currently attached passes produces an uniform
        with that name """

        for renderPass in self.renderPasses.values():
            outputs = renderPass.getOutputs()
            if uniformName in outputs.keys():
                self.debug(renderPass,"produces value",uniformName)
                return True
        return False

    def setShaders(self):
        """ Sets the shaders on all passes, by effectively calling setShaders on
        each registered RenderPass """
        for renderPass in self._sortedNodes:
            renderPass.setShaders()

    def preRenderUpdate(self):
        """ Calls the preRenderUpdate on each assigned pass """
        for renderPass in self._sortedNodes:
            renderPass.preRenderUpdate()

    def writeAutoconfig(self):
        """ Writes the shader auto config, based on the defines specified by the
        different passes """

        self.debug("Writing shader autoconfig")

        # Generate autoconfig as string
        output = "#pragma once\n"
        output += "// Autogenerated by RenderingPipeline\n"
        output += "// Do not edit! Your changes will be lost.\n\n"

        for key, value in sorted(self.defines.items()):
            output += "#define " + key + " " + str(value) + "\n"

        # output += "#define RANDOM_TIMESTAMP " + str(time.time()) + "\n"

        # Try to write the file
        try:
            with open("PipelineTemp/ShaderAutoConfig.include", "w") as handle:
                handle.write(output)
        except Exception, msg:
            self.fatal("Error writing shader autoconfig. Maybe no write-access?")
            return

    def createPasses(self):
        """ This method takes the list of RenderPasses and brings them into an
        order in which they can be rendered sequentially. After that, it creates
        all passes and sets the uniforms. """

        self._matchBuffer = self.renderPasses.values()
        self._sortedNodes = []
        self._availableUniformNames = []

        # When there is no valid configuration, make sure no infinite loop is produced
        maxIterations = 100
        currentIterations = 0

        # Sort passes
        # http://en.wikipedia.org/wiki/Topological_sorting
        while len(self._matchBuffer) > 0:
            currentIterations += 1

            if currentIterations > maxIterations:
                self.error("Iteration count of",maxIterations,"exceeded")
                return False

            for renderPass in self._matchBuffer:
                if self._canAttach(renderPass):
                    self._sortedNodes.append(renderPass)
                    self._matchBuffer.remove(renderPass)
                    self._makeUniformsAvailable(renderPass)
                    break

        # Create passes
        self._availableUniforms = {}

        # Create passes by iterating over the sorted lists
        for renderPass in self._sortedNodes:

            renderPass.create()

            # Add the defines the render pass provides
            for key, val in renderPass.getDefines().items():
                self.registerDefine(key, val)


            # Set required inputs for the pass
            for inputID, inputSource in renderPass.getRequiredInputs().items():
                inputKey = inputSource

                # If multiple entries are provided, choose the first available
                if type(inputSource) == list:
                    inputKey = self._getFirstAvailableInput(inputSource)

                if inputKey in self._availableUniforms:
                    uniformValue = self._availableUniforms[inputKey]

                    if callable(uniformValue):
                        uniformValue = uniformValue()

                    if type(uniformValue) == tuple or type(uniformValue) == list:
                        renderPass.setShaderInput(inputID, *uniformValue)
                    else:
                        renderPass.setShaderInput(inputID, uniformValue)

                    continue

                # Check for variables if no uniform exists with that name
                if inputKey.startswith("Variables."):
                    variableName = inputKey.split(".")[1]

                    if variableName in self.staticVariables:
                        renderPass.setShaderInput(inputID, self.staticVariables[variableName])
                        continue

                    if variableName in self.dynamicVariables:
                        handler = self.dynamicVariables[variableName]
                        handler(renderPass, inputID)
                        continue

                self.error("Source",inputKey,"not found")


            # Register the outputs the pass provides
            for outputName, outputValue in renderPass.getOutputs().items():
                self._availableUniforms[outputName] = outputValue

        self.debug(self._sortedNodes)
