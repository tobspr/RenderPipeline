
from DebugObject import DebugObject

class RenderPass(DebugObject):

    """ Abstract class which defines a RenderPass. This is used by the
    RenderPassMatcher. Each pass has to derive from this class """

    def __init__(self):
        DebugObject.__init__(self, self.getID())

    def getID(self):
        """ This method should return a unique identifier for the render pass """
        raise NotImplementedError()

    def getRequiredInputs(self):
        """ This method should return a dictionary with inputs required to render
        the scene pass, where the key is the name under which uniform will be
        available in the shader and the value is the source of the uniform """
        return {}

    def setShaders(self):
        """ This method will be called every time a change to the shaders is made.
        The render pass should regenerate its shaders and initial states here, and
        return all generated shaders. The render pass manager then checks all shader
        objects, and will warn the user if a shader did not compile. """
        return []

    def create(self):
        """ This method will be called during the pipeline setup. The render pass
        should setup all required RenderTargets here """
        raise NotImplementedError()

    def getDefines(self):
        """ If the pass wants to pass additional defines to the shaders, this method
        should return them, where the key is the name of the define and the value
        is the assigned value """
        return {}

    def getOutputs(self):
        """ This method should return a dictionary of outputs which are made
        available by this shader. Each input *must* start with the name of the
        RenderPass, e.g. "DeferredScenePass.depthTex". The key of the dictionary
        will determine the name of the output, whereas the value presents the output.

        Important Note: The output value has to be a lambda, e.g.
        lambda: self.target.getColorTexture(), as this function gets called during
        the render pass ordering where create() was not called yet. """
        return {}

    def preRenderUpdate(self):
        """ This method gets called before every frame, and can be overridden by
        the RenderPass """
        pass

    def setShaderInput(self, name, value, *args):
        """ This method will get called for every input specified in
        getRequiredInputs. By default, it is a assumed that the default render
        target is stored as class attribute with the name target. If it is not,
        this method should be overridden. """

        if hasattr(self, "target"):
            self.target.setShaderInput(name, value, *args)
        else:
            self.error("Your render pass has no target. You have to override setShaderInput.")

    def __repr__(self):
        """ Returns a representative string of the pass """
        return "#" + self.getID()
