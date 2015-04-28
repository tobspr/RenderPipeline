

from panda3d.core import Texture

from DebugObject import DebugObject
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from BetterShader import BetterShader
from Globals import Globals
from AbstractMethodException import AbstractMethodException

__all__ = ["AmbientOcclusionTechniqueNone", "AmbientOcclusionTechniqueSAO", "AmbientOcclusionTechniqueHBAO"]

class AmbientOcclusionTechnique(DebugObject):

    """ Abstract ambient occlusion class. All supported ao
     methods have to implement the methods this class
     defines. The sense of this class is to make it easy to
     switch between different occlusion methods. The pipeline
     can simply create another instance. There is just some work
     to be done in shaders. """

    def __init__(self, techniqueName):
        """ Subclasses should call this, techniqueName should be a
        descriptive name of the technique, e.g. SSDO """
        DebugObject.__init__(self, "AmbientOcclusion-" + techniqueName)

    def requiresViewSpacePosNrm(self):
        """ This method returns wheter the technique needs view-space
        normals and position for computing the ambient occlusion. If so,
        the pipeline will create a separate render pass to create them """
        raise AbstractMethodException()

    def requiresBlurring(self):
        """ Wheter the occlusion result should be blurred afterwards. """
        raise AbstractMethodException()

    def getIncludeName(self):
        """ Should return an identifier for the occlusion technique used in
        Shader/Occlusion/Init.include """
        raise AbstractMethodException()

    def hasSeparatePass(self):
        """ Returns wheter the occlusion has a separate pass """
        raise AbstractMethodException()

class AmbientOcclusionTechniqueNone(AmbientOcclusionTechnique):

    """ No ambient occlusion """

    def __init__(self):
        """ See parent-class """
        AmbientOcclusionTechnique.__init__(self, "None")

    def requiresViewSpacePosNrm(self):
        """ See parent-class """
        return False

    def requiresBlurring(self):
        """ See parent-class """
        return False

    def getIncludeName(self):
        """ See parent-class """
        return "NONE"

    def hasSeparatePass(self):
        """ See parent-class """
        return False

class AmbientOcclusionTechniqueSAO(AmbientOcclusionTechnique):

    """ SAO (Scalable Ambient Obscurance) """

    def __init__(self):
        """ See parent-class """
        AmbientOcclusionTechnique.__init__(self, "SAO")

    def requiresViewSpacePosNrm(self):
        """ See parent-class """
        return True

    def requiresBlurring(self):
        """ See parent-class """
        return True

    def getIncludeName(self):
        """ See parent-class """
        return "SAO"

    def hasSeparatePass(self):
        """ See parent-class """
        return True

class AmbientOcclusionTechniqueHBAO(AmbientOcclusionTechnique):

    """ HBAO (Horizon Based Ambient Occlusion) """

    def __init__(self):
        """ See parent-class """
        AmbientOcclusionTechnique.__init__(self, "HBAO")

    def requiresViewSpacePosNrm(self):
        """ See parent-class """
        return True

    def requiresBlurring(self):
        """ See parent-class """
        return True

    def getIncludeName(self):
        """ See parent-class """
        return "HBAO"

    def hasSeparatePass(self):
        """ See parent-class """
        return True