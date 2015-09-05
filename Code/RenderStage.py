
from panda3d.core import Shader

from Util.DebugObject import DebugObject
from Util.RenderTarget import RenderTarget
from Util.FunctionDecorators import protected

class RenderStage(DebugObject):

    """ This class is the abstract class for all stages used in the pipeline.
    It represents a part of the pipeline render process. Each stage specifies
    which pipes it uses and which pipes it produces. A pipe can be seen as a 
    texture, which gets modified. E.g. the gbuffer pass produces the gbuffer pipe,
    the ambient occlusion pass produces the occlusion pipe and so on. The lighting
    pass can then specify which pipes it needs and compute the image. Using
    a pipe system ensures that new techniques can be inserted easily, without
    the other techniques even being aware of them """

    def __init__(self, name, pipeline):
        """ Creates a new render stage """
        DebugObject.__init__(self, name)
        self.pipeline = pipeline
        self.targets = {}

    def getRequiredInputs(self):
        """ This method should return which shader inputs are required for this
        stage, where the key specifies the name they will be available in the shader,
        and the value specifies the name of the variable """
        return {}

    def getInputPipes(self):
        """ This method should return which pipes are required for this stage.
        The key specifies the name under they will be available in the shader,
        while the value specifies the name of the pipe """ 
        return []

    def getProducedPipes(self):
        """ This method should return which pipes this pass produces, the key
        specifies the name of the pipe, the value should be a handle to a Texture() """
        return {}

    def getProducedInputs(self):
        """ This method should return all shader inputs which the pass returns """
        return {}

    def getProducedDefines(self):
        """ This method should return all the defines which the pass produces """
        return {}

    def create(self):
        """ This method should setup the stage and create the pipes """ 
        raise NotImplementedError()

    def resize(self):
        """ This method gets called when the window resizes and should upate the
        pipes """
        raise NotImplementedError()

    def cleanup(self):
        """ This method should completely cleanup the stage and delete all used
        textures and render passes """
        raise NotImplementedError()

    def setShaders(self):
        """ This method should set all required shaders, there should be no shaders
        set in the create method, because the shader auto config is not generated
        there """
        pass

    def setShaderInput(self, *args):
        """ This method sets a shader input on all stages, which is mainly used
        by the stage manager """
        for target in self.targets.values():
            target.setShaderInput(*args)

    def update(self):
        """ This method gets called every frame """
        pass

    @protected
    def _createTarget(self, name):
        """ Creates a new render target with the given name and attachs it to the
        list of targets """
        self.targets[name] = RenderTarget(name)
        return self.targets[name]

    @protected
    def _loadShader(self, *args):
        if len(args) == 1:
            return Shader.load(Shader.SLGLSL, "Shader/DefaultPostProcess.vertex", 
                "Shader/" + args[0])  
        elif len(args) == 2:
            return Shader.load(Shader.SLGLSL, "Shader/"+ args[0], "Shader/" + args[1])
        else:
            return Shader.load(Shader.SLGLSL, "Shader/" + args[0], "Shader/" + args[1], "Shader/" + args[2])
